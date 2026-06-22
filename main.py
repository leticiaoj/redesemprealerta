from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os

app = Flask(__name__)

# Configura a chave secreta usando variáveis de ambiente (essencial para a nuvem)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_para_sessoes_escoteiras')

# =========================================================================
# 🔴 CONEXÃO COM O BANCO DE DADOS (Configurada para Local e Nuvem)
# =========================================================================
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'root'),
        database=os.environ.get('DB_NAME', 'rede_sempre_alerta'),
        cursorclass=pymysql.cursors.DictCursor
    )
# =========================================================================

@app.route('/')
def home():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Exibe apenas pedidos Ativos no feed principal
        cursor.execute("SELECT * FROM necessidades WHERE status = 'Ativo' ORDER BY data_criacao DESC")
        necessidades = cursor.fetchall()
    conn.close()
    return render_template('home.html', necessidades=necessidades)

@app.route('/cadastro_usuario', methods=['POST'])
def cadastro_usuario():
    if request.method == 'POST':
        registro = request.form['regRegistro']
        nome = request.form['regNome']
        grupo = request.form['regGrupo']
        email = request.form['regEmail']
        telefone = request.form['regTelefone']
        rede_social = request.form.get('regRedeSocial', '')
        site = request.form.get('regSite', '')
        senha = request.form['regSenha']
        
        senha_hash = generate_password_hash(senha)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = """INSERT INTO usuarios (registro_escoteiro, nome_completo, grupo_escoteiro, email, telefone, rede_social, site, senha) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (registro, nome, grupo, email, telefone, rede_social, site, senha_hash))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça seu login.', 'success')
        except pymysql.err.IntegrityError:
            flash('Erro: Registro Escoteiro ou E-mail já cadastrado.', 'danger')
            
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        registro = request.form['loginRegistro']
        senha = request.form['loginSenha']
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE registro_escoteiro = %s", (registro,))
            usuario = cursor.fetchone()
        conn.close()
        
        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['nome'] = usuario['nome_completo']
            session['registro'] = usuario['registro_escoteiro']
            session['grupo'] = usuario['grupo_escoteiro']
            session['email'] = usuario['email']
            session['telefone'] = usuario['telefone']
            session['rede_social'] = usuario['rede_social']
            session['site'] = usuario['site']
            flash(f'Sempre Alerta, {usuario["nome_completo"]}!', 'success')
            return redirect(url_for('perfil'))
        else:
            flash('Registro Escoteiro ou senha incorretos.', 'danger')
            
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))

@app.route('/cadastrar_necessidade', methods=['POST'])
def cadastrar_necessidade():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para cadastrar um pedido.', 'danger')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        grupo = request.form['grupo']
        categoria = request.form['categoria']
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        localidade = request.form['localidade']
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO necessidades (usuario_id, grupo_escoteiro, categoria, titulo, descricao, localidade) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (session['usuario_id'], grupo, categoria, titulo, descricao, localidade))
        conn.commit()
        conn.close()
        
        flash('Pedido de apoio publicado com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/apoiar/<int:necessidade_id>')
def apoiar(necessidade_id):
    if 'usuario_id' not in session:
        flash('Você precisa fazer login para oferecer apoio.', 'danger')
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO apoios (usuario_id, necessidade_id) VALUES (%s, %s)"
            cursor.execute(sql, (session['usuario_id'], necesidad_id))
            cursor.execute(sql, (session['usuario_id'], necessidade_id))
        conn.commit()
        flash('Obrigado! Você se prontificou a apoiar este pedido. Verifique os contatos na Minha Área.', 'success')
    except pymysql.err.IntegrityError:
        flash('Você já está apoiando esta necessidade!', 'warning')
    finally:
        conn.close()
        
    return redirect(url_for('home'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        flash('Acesso restrito. Faça login primeiro.', 'danger')
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    
    if request.method == 'POST':
        nome = request.form['editNome']
        registro = request.form['editRegistro']
        grupo = request.form['editGrupo']
        email = request.form['editEmail']
        telefone = request.form['editTelefone']
        rede_social = request.form.get('editRedeSocial', '')
        site = request.form.get('editSite', '')
        senha = request.form['editSenha']
        
        with conn.cursor() as cursor:
            if senha:
                senha_hash = generate_password_hash(senha)
                sql = """UPDATE usuarios SET nome_completo=%s, registro_escoteiro=%s, grupo_escoteiro=%s, email=%s, telefone=%s, rede_social=%s, site=%s, senha=%s 
                         WHERE id=%s"""
                cursor.execute(sql, (nome, registro, grupo, email, telefone, rede_social, site, senha_hash, session['usuario_id']))
            else:
                sql = """UPDATE usuarios SET nome_completo=%s, registro_escoteiro=%s, grupo_escoteiro=%s, email=%s, telefone=%s, rede_social=%s, site=%s 
                         WHERE id=%s"""
                cursor.execute(sql, (nome, registro, grupo, email, telefone, rede_social, site, session['usuario_id']))
        conn.commit()
        
        session['nome'] = nome
        session['registro'] = registro
        session['grupo'] = grupo
        session['email'] = email
        session['telefone'] = telefone
        session['rede_social'] = rede_social
        session['site'] = site
        flash('Informações cadastrais atualizadas com sucesso!', 'success')
        
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM necessidades WHERE usuario_id = %s", (session['usuario_id'],))
        minhas_necessidades = cursor.fetchall()
        
    with conn.cursor() as cursor:
        sql = """
            SELECT n.grupo_escoteiro, n.titulo, u.email, u.telefone, u.rede_social, u.site 
            FROM apoios a
            JOIN necessidades n ON a.necessidade_id = n.id
            JOIN usuarios u ON n.usuario_id = u.id
            WHERE a.usuario_id = %s
        """
        cursor.execute(sql, (session['usuario_id'],))
        meus_apoios = cursor.fetchall()
        
    conn.close()
    return render_template('perfil.html', minhas_necessidades=minhas_necessidades, meus_apoios=meus_apoios)

@app.route('/alterar_status/<int:necessidade_id>/<string:novo_status>')
def alterar_status(necessidade_id, novo_status):
    if 'usuario_id' not in session:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('home'))
        
    if novo_status not in ['Ativo', 'Encerrado']:
        flash('Status inválido.', 'danger')
        return redirect(url_for('perfil'))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "UPDATE necessidades SET status = %s WHERE id = %s AND usuario_id = %s"
        cursor.execute(sql, (novo_status, necessidade_id, session['usuario_id']))
    conn.commit()
    conn.close()
    
    flash(f'Status do pedido alterado para {novo_status}!', 'success')
    return redirect(url_for('perfil'))

@app.route('/excluir_necessidade/<int:necessidade_id>')
def excluir_necessidade(necessidade_id):
    if 'usuario_id' not in session:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('home'))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "DELETE FROM necessidades WHERE id = %s AND usuario_id = %s"
        cursor.execute(sql, (necessidade_id, session['usuario_id']))
    conn.commit()
    conn.close()
    
    flash('Pedido deletado com sucesso!', 'success')
    return redirect(url_for('perfil'))

if __name__ == '__main__':
    # Em produção (Render), o servidor usa o gunicorn. Localmente, roda em modo debug.
    app.run(debug=True)