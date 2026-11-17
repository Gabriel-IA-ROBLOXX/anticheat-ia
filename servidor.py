from flask import Flask, request, jsonify, render_template_string
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "anticheat.db"

SENHA_DONO = os.environ.get("SENHA_DONO", "G@BR1EL#._")
ROTA_ADMIN = "/" + os.environ.get("ROTA_ADMIN", "corinthians").lstrip("/")

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
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aegis IA — Anti-Cheat Inteligente para Roblox</title>
    {% if cliente %}<meta http-equiv="refresh" content="25">{% endif %}
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { margin: 0; background: radial-gradient(circle at top, #131b2e 0%, #090d16 100%); color: #e2e8f0; min-height: 100vh; padding: 30px 15px; }
        .container { max-width: 960px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.2rem; margin: 0; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #94a3b8; margin-top: 6px; font-size: 0.95rem; }
        .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 14px; padding: 24px; margin-bottom: 22px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #f8fafc; font-size: 1.15rem; border-bottom: 1px solid rgba(148, 163, 184, 0.15); padding-bottom: 12px; }
        .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        input[type=text], input[type=password], input[type=number], select { background: #0f172a; border: 1px solid #334155; color: #f8fafc; padding: 10px 14px; border-radius: 8px; font-size: 0.95rem; outline: none; }
        input:focus, select:focus { border-color: #38bdf8; }
        button { background: linear-gradient(135deg, #2563eb, #4f46e5); color: white; border: none; padding: 11px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .btn-green { background: linear-gradient(135deg, #059669, #10b981); }
        .btn-red { background: linear-gradient(135deg, #dc2626, #ef4444); padding: 6px 12px; font-size: 0.85rem; }
        .grid-inputs { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin: 18px 0; }
        .input-box label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 5px; text-transform: uppercase; }
        .input-box input { width: 100%; font-weight: bold; text-align: center; font-size: 1.05rem; }
        .toggles { display: flex; gap: 20px; flex-wrap: wrap; background: #0f172a; padding: 14px; border-radius: 8px; margin-bottom: 18px; }
        .toggles label { cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 0.92rem; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { text-align: left; padding: 12px; color: #94a3b8; font-size: 0.82rem; text-transform: uppercase; border-bottom: 1px solid #334155; }
        td { padding: 12px; border-bottom: 1px solid rgba(51, 65, 85, 0.5); font-size: 0.92rem; }
        .badge-ban { background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        .badge-obs { background: rgba(245, 158, 11, 0.2); color: #fcd34d; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        .status-live { display: inline-block; width: 9px; height: 9px; background: #10b981; border-radius: 50%; margin-right: 6px; box-shadow: 0 0 8px #10b981; }
        @media (max-width: 768px) {
            body { padding: 18px 10px; }
            .header h1 { font-size: 2.1rem; }
            .card { padding: 20px 16px; }
            input[type=text], input[type=password], input[type=number], select, button { width: 100% !important; font-size: 1.15rem; padding: 15px; }
            .btn-red { width: auto !important; padding: 8px 14px; font-size: 0.95rem; }
            .grid-inputs { grid-template-columns: repeat(2, 1fr); gap: 12px; }
            .toggles { flex-direction: column; gap: 16px; }
            .toggles input[type=checkbox] { width: 22px; height: 22px; }
            th, td { font-size: 1rem; padding: 12px 8px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🛡️ Aegis IA — Cloud Anti-Cheat</h1>
        <p>Proteção comportamental em tempo real com auto-calibração neural para Roblox</p>
    </div>

    {% if not admin_mode %}
    <div class="card">
        <form method="GET" action="/" class="row" style="justify-content: center;">
            <input type="text" name="chave" value="{{ chave }}" placeholder="Insira sua Chave de Licença..." style="width: 280px;">
            <button type="submit">Acessar Painel</button>
        </form>
        {% if erro %}<p style="color:#f87171; text-align:center; margin-bottom:0;">{{ erro }}</p>{% endif %}
    </div>
    {% endif %}

    {% if admin_mode %}
    <div class="card" style="border-color: #38bdf8;">
        <h3>🔑 Central do Administrador (Criar e Gerenciar Clientes)</h3>
        <form method="POST" action="{{ rota_admin }}/criar" class="row">
            <input type="password" name="senha_admin" value="{{ senha_digitada }}" placeholder="Senha Mestra" required>
            <input type="text" name="novo_nome" placeholder="Nome do Jogo do Cliente" required>
            <input type="text" name="nova_chave" placeholder="Nova Chave (ex: VIP_01)" required>
            <button type="submit" class="btn-green">+ Gerar Licença</button>
        </form>
        {% if erro %}<p style="color:#f87171; margin-bottom:0;">{{ erro }}</p>{% endif %}
        {% if sucesso %}<p style="color:#34d399; margin-bottom:0; font-weight:bold;">{{ sucesso }}</p>{% endif %}
    </div>

    <div class="card">
        <h3>📋 Clientes Ativos no Sistema</h3>
        <form method="POST" action="{{ rota_admin }}" class="row" style="margin-bottom:15px;">
            <input type="password" name="senha_admin" value="{{ senha_digitada }}" placeholder="Digite sua Senha Mestra para listar/revogar">
            <button type="submit">Desbloquear Lista</button>
        </form>
        {% if lista_clientes %}
        <div class="table-wrap">
            <table>
                <tr><th>Jogo</th><th>Chave</th><th>Categoria</th><th>Ação</th></tr>
                {% for c in lista_clientes %}
                <tr>
                    <td><strong>{{ c['nome_cliente'] }}</strong></td>
                    <td style="color:#38bdf8;">{{ c['chave'] }}</td>
                    <td>{{ c['modo'] }}</td>
                    <td>
                        <form method="POST" action="{{ rota_admin }}/revogar" style="margin:0;">
                            <input type="hidden" name="senha_admin" value="{{ senha_digitada }}">
                            <input type="hidden" name="chave_alvo" value="{{ c['chave'] }}">
                            <button type="submit" class="btn-red">Revogar</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>
    {% endif %}
    {% if cliente %}
    <div class="card">
        <div class="row" style="justify-content: space-between; border-bottom: 1px solid rgba(148,163,184,0.15); padding-bottom: 12px; margin-bottom: 16px;">
            <h3 style="border:none; margin:0; padding:0;">🎮 {{ cliente['nome_cliente'] }}</h3>
            <span style="font-size: 0.9rem; color: #94a3b8;"><span class="status-live"></span>Proteção Ativa (Atualiza a cada 25s)</span>
        </div>

        <form method="POST" action="/salvar_config">
            <input type="hidden" name="chave" value="{{ chave }}">
            <div class="row">
                <label style="color:#94a3b8;">Predefinição por Gênero:</label>
                <select name="modo">
                    <option value="TYCOON" {% if cliente['modo']=='TYCOON' %}selected{% endif %}>1. Tycoon (Bases e Fábricas)</option>
                    <option value="SIMULADOR" {% if cliente['modo']=='SIMULADOR' %}selected{% endif %}>2. Simulador (Pets e Cliques)</option>
                    <option value="OBBY" {% if cliente['modo']=='OBBY' %}selected{% endif %}>3. Obby (Parkour Rígido)</option>
                    <option value="SUPER_HEROI" {% if cliente['modo']=='SUPER_HEROI' %}selected{% endif %}>4. Super-Herói (Voo e Alta Velocidade)</option>
                </select>
                <button type="submit" name="acao_btn" value="aplicar_perfil">Aplicar Perfil</button>
            </div>

            <div class="grid-inputs">
                <div class="input-box"><label>Velocidade Máx</label><input type="number" name="vel_max" value="{{ cliente['vel_max'] }}"></div>
                <div class="input-box"><label>Dist. Teleporte</label><input type="number" name="teleporte_dist" value="{{ cliente['teleporte_dist'] }}"></div>
                <div class="input-box"><label>Altura Pulo</label><input type="number" name="altura_pulo_max" value="{{ cliente['altura_pulo_max'] }}"></div>
                <div class="input-box"><label>Pulos no Ar</label><input type="number" name="pulos_ar_max" value="{{ cliente['pulos_ar_max'] }}"></div>
                <div class="input-box"><label>Cliques/Seg (CPS)</label><input type="number" name="cps_max" value="{{ cliente['cps_max'] }}"></div>
            </div>

            <div class="toggles">
                <label><input type="checkbox" name="ia" {% if cliente['ia_ativa'] %}checked{% endif %}> 🤖 IA Comportamental</label>
                <label><input type="checkbox" name="aprendizado" {% if cliente['modo_aprendizado'] %}checked{% endif %}> 🧠 Auto-Calibrar Limites</label>
                <label><input type="checkbox" name="obs" {% if cliente['modo_observacao'] %}checked{% endif %}> 👁️ Modo Observação (Só alertar)</label>
            </div>

            <button type="submit" name="acao_btn" value="salvar_tudo" class="btn-green">💾 Salvar Configurações</button>
        </form>
    </div>

    <div class="card">
        <h3>🚨 Registro de Ameaças Bloqueadas</h3>
        <div class="table-wrap">
            <table>
                <tr><th>Horário</th><th>Jogador</th><th>Infração Detectada</th><th>Status</th></tr>
                {% for log in logs %}
                <tr>
                    <td style="color:#94a3b8;">{{ log['hora'] }}</td>
                    <td><strong>{{ log['user'] }}</strong></td>
                    <td>{{ log['motivo'] }}</td>
                    <td><span class="{{ 'badge-ban' if log['acao'] == 'BANIDO' else 'badge-obs' }}">{{ log['acao'] }}</span></td>
                </tr>
                {% else %}
                <tr><td colspan="4" style="text-align:center; color:#64748b; padding: 25px;">Nenhuma tentativa de trapaça registrada neste jogo até o momento.</td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
    {% endif %}
</div>
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
            erro = "Chave de licença inválida ou não encontrada."
    return render_template_string(HTML_PAINEL, chave=chave, cliente=cliente, logs=logs, erro=erro, admin_mode=False)

@app.route(ROTA_ADMIN, methods=["GET", "POST"])
def painel_admin():
    senha = request.form.get("senha_admin", "")
    erro = ""
    lista_clientes = []
    if request.method == "POST":
        if senha == SENHA_DONO:
            conn = get_db()
            lista_clientes = conn.execute("SELECT chave, nome_cliente, modo FROM clientes").fetchall()
            conn.close()
        else:
            erro = "Senha Mestra incorreta!"
    return render_template_string(HTML_PAINEL, chave="", cliente=None, logs=[], erro=erro, sucesso="", admin_mode=True, rota_admin=ROTA_ADMIN, senha_digitada=senha, lista_clientes=lista_clientes)

@app.route(ROTA_ADMIN + "/criar", methods=["POST"])
def criar_cliente():
    senha = request.form.get("senha_admin", "")
    if senha != SENHA_DONO:
        return render_template_string(HTML_PAINEL, chave="", cliente=None, logs=[], erro="Senha Mestra incorreta!", sucesso="", admin_mode=True, rota_admin=ROTA_ADMIN, senha_digitada="", lista_clientes=[])
    
    nome = request.form.get("novo_nome")
    nova_chave = request.form.get("nova_chave").strip()
    sucesso = ""
    erro = ""
    conn = get_db()
    if nova_chave:
        try:
            conn.execute("INSERT INTO clientes VALUES (?, ?, 'TYCOON', 24, 65, 1, 12, 12, 0, 0, 1)", (nova_chave, nome))
            conn.commit()
            sucesso = f"Licença '{nova_chave}' criada para '{nome}'! Você continua no painel de Dono."
        except sqlite3.IntegrityError:
            erro = "Essa chave já existe! Escolha outro código."
    lista_clientes = conn.execute("SELECT chave, nome_cliente, modo FROM clientes").fetchall()
    conn.close()
    return render_template_string(HTML_PAINEL, chave="", cliente=None, logs=[], erro=erro, sucesso=sucesso, admin_mode=True, rota_admin=ROTA_ADMIN, senha_digitada=senha, lista_clientes=lista_clientes)

@app.route(ROTA_ADMIN + "/revogar", methods=["POST"])
def revogar_cliente():
    senha = request.form.get("senha_admin", "")
    chave_alvo = request.form.get("chave_alvo", "")
    if senha == SENHA_DONO and chave_alvo:
        conn = get_db()
        conn.execute("DELETE FROM clientes WHERE chave = ?", (chave_alvo,))
        conn.execute("DELETE FROM logs WHERE chave = ?", (chave_alvo,))
        conn.commit()
        lista_clientes = conn.execute("SELECT chave, nome_cliente, modo FROM clientes").fetchall()
        conn.close()
        return render_template_string(HTML_PAINEL, chave="", cliente=None, logs=[], erro="", sucesso=f"Chave '{chave_alvo}' revogada e removida!", admin_mode=True, rota_admin=ROTA_ADMIN, senha_digitada=senha, lista_clientes=lista_clientes)
    return "Acesso negado", 403

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

    mapa_cliente = suspeitas_memoria.setdefault(chave, {})
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

        pts_atuais = mapa_cliente.get(chave_jog, 0)
        motivos = []

        if vel >= cli["teleporte_dist"]:
            pts_atuais += 100
            motivos.append(f"Teleporte ({vel})")
        elif vel > cli["vel_max"]:
            pts_atuais += 40
            motivos.append(f"Velocidade ({vel})")

        if altura_pulo > cli["altura_pulo_max"]:
            pts_atuais += 50
            motivos.append(f"Super Pulo ({altura_pulo})")

        if pulos > cli["pulos_ar_max"]:
            pts_atuais += 40
            motivos.append(f"Pulo Infinito ({pulos}x)")

        if cps > cli["cps_max"] and var_clique < 15:
            pts_atuais += 50
            motivos.append(f"Auto-Clicker ({cps} CPS)")

        if cli["ia_ativa"] and not motivos and vel > 0:
            pred = modelo_ia.predict(np.array([(vel, pulos, var_clique)]))
            if pred == -1:
                pts_atuais += 15
                motivos.append("Anomalia IA")

        if not motivos:
            pts_atuais = max(0, pts_atuais - 4)

        if pts_atuais >= 100:
            motivo_txt = " + ".join(motivos)
            hora = datetime.now().strftime("%H:%M:%S")
            if cli["modo_observacao"]:
                conn.execute("INSERT INTO logs (chave, hora, user, motivo, acao) VALUES (?, ?, ?, ?, 'OBSERVADO')", (chave, hora, chave_jog, motivo_txt))
                acoes_resposta[user_id] = {"acao": "ALERTA", "motivo": motivo_txt}
            else:
                conn.execute("INSERT INTO logs (chave, hora, user, motivo, acao) VALUES (?, ?, ?, ?, 'BANIDO')", (chave, hora, chave_jog, motivo_txt))
                acoes_resposta[user_id] = {"acao": "BANIR", "motivo": motivo_txt}
            pts_atuais = 0

        mapa_cliente[chave_jog] = pts_atuais

    conn.commit()
    conn.close()
    return jsonify({"acoes": acoes_resposta})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
