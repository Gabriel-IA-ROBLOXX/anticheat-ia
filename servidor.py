from flask import Flask, request, jsonify, render_template_string
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "anticheat.db"

# SUA SENHA SECRETA DE DONO (Mude se quiser, só você sabe ela)
SENHA_DONO = "GABRIEL_DONO_2026"

PERFIS_PADRAO = {
    "TYCOON": {"vel_max": 24, "teleporte_dist": 65, "pulos_ar_max": 1, "altura_pulo_max": 12, "cps_max": 12},
    "SIMULADOR": {"vel_max": 60, "teleporte_dist": 120, "pulos_ar_max": 2, "altura_pulo_max": 25, "cps_max": 18},
    "OBBY": {"vel_max": 20, "teleporte_dist": 50, "pulos_ar_max": 1, "altura_pulo_max": 10, "cps_max": 10},
    "SUPER_HEROI": {"vel_max": 150, "teleporte_dist": 300, "pulos_ar_max": 15, "altura_pulo_max": 120, "cps_max": 20}
}

suspeitas_memoria = {}

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS clientes (
        chave TEXT PRIMARY KEY, nome_cliente TEXT, modo TEXT,
        vel_max INTEGER, teleporte_dist INTEGER, pulos_ar_max INTEGER,
        altura_pulo_max INTEGER, cps_max INTEGER,
        modo_observacao INTEGER, modo_aprendizado INTEGER, ia_ativa INTEGER
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chave TEXT, hora TEXT,
        user TEXT, motivo TEXT, acao TEXT
    )''')
    cur = conn.execute("SELECT chave FROM clientes WHERE chave = 'CHAVE_DEMO_2026'")
    if not cur.fetchone():
        conn.execute("INSERT INTO clientes VALUES ('CHAVE_DEMO_2026', 'Meu Jogo Teste', 'TYCOON', 24, 65, 1, 12, 12, 0, 0, 1)")
    conn.commit()
    conn.close()

init_db()

lista_treino = (
    (16, 0, 120), (16, 1, 95), (18, 0, 150), (0, 0, 200),
    (15, 1, 80), (20, 1, 110), (12, 0, 140), (16, 0, 60)
)
modelo_ia = IsolationForest(contamination=0.1, random_state=42)
modelo_ia.fit(np.array(lista_treino))

HTML_PAINEL = """
<!DOCTYPE html>
<html>
<head>
    <title>Anti-Cheat IA Cloud 4.1</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; padding: 20px; background: #0d1117; color: #c9d1d9; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 15px; }
        h1, h3 { color: #58a6ff; margin-top: 0; }
        input, select { padding: 8px; border-radius: 5px; border: 1px solid #30363d; background: #21262d; color: white; margin: 4px; }
        button { padding: 9px 15px; border-radius: 5px; background: #238636; color: white; border: none; font-weight: bold; cursor: pointer; }
        .btn-red { background: #da3633; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #30363d; }
        .ban { color: #ff7b72; font-weight: bold; }
        .obs { color: #d29922; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🛡️ Anti-Cheat IA Cloud</h1>
        <form method="GET" action="/">
            Chave do Cliente: <input type="text" name="chave" value="{{ chave }}" placeholder="Cole sua chave aqui">
            <button type="submit">Acessar Painel</button>
        </form>
        <hr style="border-color: #30363d; margin: 15px 0;">
        <form method="POST" action="/novo_cliente">
            <strong>Área do Administrador:</strong><br>
            <input type="password" name="senha_admin" placeholder="Senha Mestra de Dono" required>
            <input type="text" name="novo_nome" placeholder="Nome do Jogo" required>
            <input type="text" name="nova_chave" placeholder="Criar Nova Chave" required>
            <button type="submit">+ Gerar Chave</button>
        </form>
        {% if erro %}<p style="color:#ff7b72;">{{ erro }}</p>{% endif %}
    </div>

    {% if cliente %}
    <div class="card">
        <h3>Jogo: {{ cliente['nome_cliente'] }}</h3>
        <form method="POST" action="/salvar_config">
            <input type="hidden" name="chave" value="{{ chave }}">
            Categoria:
            <select name="modo">
                <option value="TYCOON" {% if cliente['modo']=='TYCOON' %}selected{% endif %}>1. Tycoon</option>
                <option value="SIMULADOR" {% if cliente['modo']=='SIMULADOR' %}selected{% endif %}>2. Simulador</option>
                <option value="OBBY" {% if cliente['modo']=='OBBY' %}selected{% endif %}>3. Obby</option>
                <option value="SUPER_HEROI" {% if cliente['modo']=='SUPER_HEROI' %}selected{% endif %}>4. Super-Heroi</option>
            </select>
            <button type="submit" name="acao_btn" value="aplicar_perfil">Carregar Categoria</button><br><br>
            Vel Max: <input type="number" name="vel_max" value="{{ cliente['vel_max'] }}" style="width:70px;">
            Teleporte: <input type="number" name="teleporte_dist" value="{{ cliente['teleporte_dist'] }}" style="width:70px;">
            Altura Pulo: <input type="number" name="altura_pulo_max" value="{{ cliente['altura_pulo_max'] }}" style="width:70px;">
            Pulos Ar: <input type="number" name="pulos_ar_max" value="{{ cliente['pulos_ar_max'] }}" style="width:70px;">
            CPS Max: <input type="number" name="cps_max" value="{{ cliente['cps_max'] }}" style="width:70px;"><br><br>
            <label><input type="checkbox" name="ia" {% if cliente['ia_ativa'] %}checked{% endif %}> IA Ativa</label>
            <label><input type="checkbox" name="aprendizado" {% if cliente['modo_aprendizado'] %}checked{% endif %}> Auto-Calibrar Tudo</label>
            <label><input type="checkbox" name="obs" {% if cliente['modo_observacao'] %}checked{% endif %}> Modo Observacao</label><br><br>
            <button type="submit" name="acao_btn" value="salvar_tudo">Salvar Ajustes</button>
        </form>
    </div>

    <div class="card">
        <h3>Historico Salvo no Banco de Dados</h3>
        <table>
            <tr><th>Hora</th><th>Jogador</th><th>Motivo</th><th>Acao</th></tr>
            {% for log in logs %}
            <tr>
                <td>{{ log['hora'] }}</td>
                <td>{{ log['user'] }}</td>
                <td>{{ log['motivo'] }}</td>
                <td class="{{ 'ban' if log['acao'] == 'BANIDO' else 'obs' }}">{{ log['acao'] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def painel():
    chave = request.args.get("chave", "")
    erro = request.args.get("erro", "")
    cliente = None
    logs = []
    if chave:
        conn = get_db()
        cliente = conn.execute("SELECT * FROM clientes WHERE chave = ?", (chave,)).fetchone()
        logs = conn.execute("SELECT * FROM logs WHERE chave = ? ORDER BY id DESC LIMIT 25", (chave,)).fetchall()
        conn.close()
        if not cliente:
            erro = "Chave invalida ou expirada!"
    return render_template_string(HTML_PAINEL, chave=chave, cliente=cliente, logs=logs, erro=erro)

@app.route("/novo_cliente", methods=["POST"])
def novo_cliente():
    senha = request.form.get("senha_admin", "")
    if senha != SENHA_DONO:
        return '<script>window.location.href="/?erro=Senha+de+Dono+Incorreta!";</script>'
    
    nome = request.form.get("novo_nome")
    nova_chave = request.form.get("nova_chave").strip()
    if nova_chave:
        conn = get_db()
        try:
            conn.execute("INSERT INTO clientes VALUES (?, ?, 'TYCOON', 24, 65, 1, 12, 12, 0, 0, 1)", (nova_chave, nome))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return f'<script>window.location.href="/?chave={nova_chave}";</script>'

@app.route("/salvar_config", methods=["POST"])
def salvar_config():
    chave = request.form.get("chave")
    acao = request.form.get("acao_btn")
    modo = request.form.get("modo")
    conn = get_db()
    if acao == "aplicar_perfil" and modo in PERFIS_PADRAO:
        p = PERFIS_PADRAO[modo]
        conn.execute("UPDATE clientes SET modo=?, vel_max=?, teleporte_dist=?, pulos_ar_max=?, altura_pulo_max=?, cps_max=? WHERE chave=?",
                     (modo, p["vel_max"], p["teleporte_dist"], p["pulos_ar_max"], p["altura_pulo_max"], p["cps_max"], chave))
    else:
        conn.execute("UPDATE clientes SET modo=?, vel_max=?, teleporte_dist=?, altura_pulo_max=?, pulos_ar_max=?, cps_max=?, modo_observacao=?, modo_aprendizado=?, ia_ativa=? WHERE chave=?",
                     (modo, int(request.form.get("vel_max", 24)), int(request.form.get("teleporte_dist", 65)),
                      int(request.form.get("altura_pulo_max", 12)), int(request.form.get("pulos_ar_max", 1)),
                      int(request.form.get("cps_max", 12)), 1 if "obs" in request.form else 0,
                      1 if "aprendizado" in request.form else 0, 1 if "ia" in request.form else 0, chave))
    conn.commit()
    conn.close()
    return f'<script>window.location.href="/?chave={chave}";</script>'

@app.route("/analisar_lote", methods=["POST"])
def analisar_lote():
    chave = request.headers.get("X-API-Key")
    conn = get_db()
    cli = conn.execute("SELECT * FROM clientes WHERE chave = ?", (chave,)).fetchone()
    if not cli:
        conn.close()
        return jsonify({"erro": "Chave invalida"}), 403

    suspeitas_memoria.setdefault(chave, {})
    acoes_resposta = {}

    for dados in request.json.get("jogadores", []):
        user_id = str(dados.get("user_id"))
        nome = dados.get("nome", "Jogador")
        chave_jog = f"{nome} ({user_id})"
        vel = dados.get("velocidade", 0)
        pulos = dados.get("pulos_no_ar", 0)
        altura_pulo = dados.get("altura_pulo", 0)
        cps = dados.get("cliques_por_segundo", 0)
        var_clique = dados.get("variacao_clique_ms", 100)

        if cli["modo_aprendizado"]:
            n_vel = vel + 5 if cli["vel_max"] < vel < 500 else cli["vel_max"]
            n_tel = vel + 45 if cli["vel_max"] < vel < 500 else cli["teleporte_dist"]
            n_alt = altura_pulo + 4 if cli["altura_pulo_max"] < altura_pulo < 300 else cli["altura_pulo_max"]
            n_pul = pulos if cli["pulos_ar_max"] < pulos < 20 else cli["pulos_ar_max"]
            n_cps = cps + 2 if (cli["cps_max"] < cps < 25 and var_clique >= 20) else cli["cps_max"]
            conn.execute("UPDATE clientes SET vel_max=?, teleporte_dist=?, altura_pulo_max=?, pulos_ar_max=?, cps_max=? WHERE chave=?",
                         (n_vel, n_tel, n_alt, n_pul, n_cps, chave))
            continue

        suspeitas_memoria[chave].setdefault(chave_jog, 0)
        motivos = []

        if vel >= cli["teleporte_dist"]:
            suspeitas_memoria[chave][chave_jog] += 100
            motivos.append(f"Teleporte ({vel})")
        elif vel > cli["vel_max"]:
            suspeitas_memoria[chave][chave_jog] += 40
            motivos.append(f"Velocidade ({vel})")

        if altura_pulo > cli["altura_pulo_max"]:
            suspeitas_memoria[chave][chave_jog] += 50
            motivos.append(f"Super Pulo ({altura_pulo})")

        if pulos > cli["pulos_ar_max"]:
            suspeitas_memoria[chave][chave_jog] += 40
            motivos.append(f"Pulo Infinito ({pulos}x)")

        if cps > cli["cps_max"] and var_clique < 15:
            suspeitas_memoria[chave][chave_jog] += 50
            motivos.append(f"Auto-Clicker ({cps} CPS)")

        if cli["ia_ativa"] and not motivos and vel > 0:
            pred = modelo_ia.predict(np.array([(vel, pulos, var_clique)]))
            if pred == -1:
                suspeitas_memoria[chave][chave_jog] += 15
                motivos.append("Anomalia IA")

        if not motivos:
            suspeitas_memoria[chave][chave_jog] = max(0, suspeitas_memoria[chave][chave_jog] - 4)

        if suspeitas_memoria[chave][chave_jog] >= 100:
            motivo_txt = " + ".join(motivos)
            hora = datetime.now().strftime("%H:%M:%S")
            if cli["modo_observacao"]:
                conn.execute("INSERT INTO logs (chave, hora, user, motivo, acao) VALUES (?, ?, ?, ?, 'OBSERVADO')", (chave, hora, chave_jog, motivo_txt))
                acoes_resposta[user_id] = {"acao": "ALERTA", "motivo": motivo_txt}
            else:
                conn.execute("INSERT INTO logs (chave, hora, user, motivo, acao) VALUES (?, ?, ?, ?, 'BANIDO')", (chave, hora, chave_jog, motivo_txt))
                acoes_resposta[user_id] = {"acao": "BANIR", "motivo": motivo_txt}
            suspeitas_memoria[chave][chave_jog] = 0

    conn.commit()
    conn.close()
    return jsonify({"acoes": acoes_resposta})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
