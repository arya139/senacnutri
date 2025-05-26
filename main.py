import sys
import mysql.connector
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, date, timedelta
import numpy as np
from PyQt5.QtCore import QTimer
import os
from config import DATABASE_CONFIG

#pip install PyQt5 mysql-connector-python matplotlib numpy

from config import DATABASE_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DATABASE_CONFIG)
            return True
        except mysql.connector.Error as e:
            QMessageBox.critical(None, "Erro de Conexão", f"Erro ao conectar com o banco: {e}")
            return False
        
    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except mysql.connector.Error as e:
            QMessageBox.critical(None, "Erro SQL", f"Erro na consulta: {e}")
            return []
    
    def execute_insert(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as e:
            QMessageBox.critical(None, "Erro SQL", f"Erro na inserção: {e}")
            return None

class PacienteDialog(QDialog):
    def __init__(self, db, paciente_data=None):
        super().__init__()
        self.db = db
        self.paciente_data = paciente_data
        self.init_ui()
        
        if paciente_data:
            self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("Cadastro de Paciente")
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout()
        
        self.nome = QLineEdit()
        self.idade = QSpinBox()
        self.idade.setRange(1, 120)
        self.sexo = QComboBox()
        self.sexo.addItems(['M', 'F'])
        self.peso = QDoubleSpinBox()
        self.peso.setRange(1, 300)
        self.peso.setDecimals(2)
        self.altura = QDoubleSpinBox()
        self.altura.setRange(0.5, 2.5)
        self.altura.setDecimals(2)
        self.historico = QTextEdit()
        self.alergias = QTextEdit()
        self.telefone = QLineEdit()
        self.email = QLineEdit()
        
        form_layout = QFormLayout()
        form_layout.addRow("Nome:", self.nome)
        form_layout.addRow("Idade:", self.idade)
        form_layout.addRow("Sexo:", self.sexo)
        form_layout.addRow("Peso (kg):", self.peso)
        form_layout.addRow("Altura (m):", self.altura)
        form_layout.addRow("Histórico Médico:", self.historico)
        form_layout.addRow("Alergias:", self.alergias)
        form_layout.addRow("Telefone:", self.telefone)
        form_layout.addRow("Email:", self.email)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar")
        self.cancel_btn = QPushButton("Cancelar")
        
        self.save_btn.clicked.connect(self.save_paciente)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        self.nome.setText(str(self.paciente_data[1]))
        self.idade.setValue(self.paciente_data[2])
        self.sexo.setCurrentText(self.paciente_data[3])
        self.peso.setValue(float(self.paciente_data[4]))
        self.altura.setValue(float(self.paciente_data[5]))
        self.historico.setPlainText(str(self.paciente_data[7]) if self.paciente_data[7] else "")
        self.alergias.setPlainText(str(self.paciente_data[8]) if self.paciente_data[8] else "")
        self.telefone.setText(str(self.paciente_data[9]) if self.paciente_data[9] else "")
        self.email.setText(str(self.paciente_data[10]) if self.paciente_data[10] else "")
    
    def save_paciente(self):
        if not self.nome.text():
            QMessageBox.warning(self, "Aviso", "Nome é obrigatório!")
            return
        
        data = (
            self.nome.text(),
            self.idade.value(),
            self.sexo.currentText(),
            self.peso.value(),
            self.altura.value(),
            self.historico.toPlainText(),
            self.alergias.toPlainText(),
            self.telefone.text(),
            self.email.text()
        )
        
        if self.paciente_data: 
            query = """UPDATE pacientes SET nome=%s, idade=%s, sexo=%s, peso=%s, altura=%s,
                    historico_medico=%s, alergias=%s, telefone=%s, email=%s WHERE id=%s"""
            self.db.execute_insert(query, data + (self.paciente_data[0],))
        else: 
            query = """INSERT INTO pacientes (nome, idade, sexo, peso, altura, historico_medico, 
                    alergias, telefone, email) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            result = self.db.execute_insert(query, data)
            
            if result:
                peso_query = """INSERT INTO historico_peso (paciente_id, peso, data_pesagem) 
                            VALUES (%s, %s, %s)"""
                self.db.execute_insert(peso_query, (result, self.peso.value(), date.today()))
        
        self.accept()
class ConsultaDialog(QDialog):
    def __init__(self, db, consulta_data=None):
        super().__init__()
        self.db = db
        self.consulta_data = consulta_data
        self.init_ui()
        
        if consulta_data:
            self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("Cadastro de Consulta")
        self.setFixedSize(500, 500)
        
        layout = QVBoxLayout()
        
        self.paciente = QComboBox()
        self.load_pacientes()
        self.data_consulta = QDateTimeEdit()
        self.data_consulta.setDateTime(QDateTime.currentDateTime())
        self.anotacoes = QTextEdit()
        self.dieta = QTextEdit()
        self.orientacoes = QTextEdit()
        self.peso_atual = QDoubleSpinBox()
        self.peso_atual.setRange(1, 300)
        self.peso_atual.setDecimals(2)
        self.status = QComboBox()
        self.status.addItems(['Agendada', 'Realizada', 'Cancelada'])
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0, 9999)
        self.valor.setDecimals(2)
        
        form_layout = QFormLayout()
        form_layout.addRow("Paciente:", self.paciente)
        form_layout.addRow("Data/Hora:", self.data_consulta)
        form_layout.addRow("Anotações:", self.anotacoes)
        form_layout.addRow("Dieta Prescrita:", self.dieta)
        form_layout.addRow("Orientações:", self.orientacoes)
        form_layout.addRow("Peso Atual:", self.peso_atual)
        form_layout.addRow("Status:", self.status)
        form_layout.addRow("Valor:", self.valor)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar")
        self.cancel_btn = QPushButton("Cancelar")
        
        self.save_btn.clicked.connect(self.save_consulta)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_pacientes(self):
        pacientes = self.db.execute_query("SELECT id, nome FROM pacientes ORDER BY nome")
        self.paciente.clear()
        for p in pacientes:
            self.paciente.addItem(f"{p[1]}", p[0])
    
    def load_data(self):
        for i in range(self.paciente.count()):
            if self.paciente.itemData(i) == self.consulta_data[1]:
                self.paciente.setCurrentIndex(i)
                break
        
        self.data_consulta.setDateTime(QDateTime.fromString(str(self.consulta_data[2]), "yyyy-MM-dd hh:mm:ss"))
        self.anotacoes.setPlainText(str(self.consulta_data[3]) if self.consulta_data[3] else "")
        self.dieta.setPlainText(str(self.consulta_data[4]) if self.consulta_data[4] else "")
        self.orientacoes.setPlainText(str(self.consulta_data[5]) if self.consulta_data[5] else "")
        if self.consulta_data[6]:
            self.peso_atual.setValue(float(self.consulta_data[6]))
        self.status.setCurrentText(self.consulta_data[7])
        if self.consulta_data[8]:
            self.valor.setValue(float(self.consulta_data[8]))
    
    def save_consulta(self):
        if self.paciente.currentData() is None:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente!")
            return
        
        data = (
            self.paciente.currentData(),
            self.data_consulta.dateTime().toString("yyyy-MM-dd hh:mm:ss"),
            self.anotacoes.toPlainText(),
            self.dieta.toPlainText(),
            self.orientacoes.toPlainText(),
            self.peso_atual.value(),
            self.status.currentText(),
            self.valor.value()
        )
        
        if self.consulta_data: 
            query = """UPDATE consultas SET paciente_id=%s, data_consulta=%s, anotacoes=%s, 
                      dieta_prescrita=%s, orientacoes=%s, peso_atual=%s, status=%s, valor=%s WHERE id=%s"""
            self.db.execute_insert(query, data + (self.consulta_data[0],))
        else: 
            query = """INSERT INTO consultas (paciente_id, data_consulta, anotacoes, dieta_prescrita, 
                      orientacoes, peso_atual, status, valor) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            result = self.db.execute_insert(query, data)
            
            if result and self.status.currentText() == 'Realizada' and self.peso_atual.value() > 0:
                peso_query = """INSERT INTO historico_peso (paciente_id, peso, data_pesagem) 
                               VALUES (%s, %s, %s)"""
                self.db.execute_insert(peso_query, (self.paciente.currentData(), 
                                                  self.peso_atual.value(), 
                                                  self.data_consulta.date().toPyDate()))
        
        self.accept()

class GraphWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        self.btn_evolucao = QPushButton("Gráfico Evolução Peso")
        self.btn_comparacao = QPushButton("Comparação Pacientes")
        self.btn_consultas_mes = QPushButton("Consultas por Mês")
        
        self.btn_evolucao.clicked.connect(self.show_evolucao_peso)
        self.btn_comparacao.clicked.connect(self.show_comparacao_pacientes)
        self.btn_consultas_mes.clicked.connect(self.show_consultas_mes)
        
        button_layout.addWidget(self.btn_evolucao)
        button_layout.addWidget(self.btn_comparacao)
        button_layout.addWidget(self.btn_consultas_mes)
        layout.addLayout(button_layout)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
    
    def show_evolucao_peso(self):
        pacientes = self.db.execute_query("SELECT id, nome FROM pacientes ORDER BY nome")
        if not pacientes:
            QMessageBox.information(self, "Info", "Nenhum paciente cadastrado!")
            return
        
        items = [f"{p[1]}" for p in pacientes]
        item, ok = QInputDialog.getItem(self, "Selecionar Paciente", "Paciente:", items, 0, False)
        
        if ok and item:
            paciente_id = None
            for p in pacientes:
                if p[1] == item:
                    paciente_id = p[0]
                    break
            
            if paciente_id:
                self.plot_evolucao_peso(paciente_id, item)
    
    def plot_evolucao_peso(self, paciente_id, nome_paciente):
        query = """SELECT data_pesagem, peso FROM historico_peso 
                  WHERE paciente_id = %s ORDER BY data_pesagem"""
        dados = self.db.execute_query(query, (paciente_id,))
        
        if not dados:
            QMessageBox.information(self, "Info", "Sem dados de peso para este paciente!")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        datas = [d[0] for d in dados]
        pesos = [float(d[1]) for d in dados]
        
        ax.plot(datas, pesos, marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax.set_title(f'Evolução de Peso - {nome_paciente}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Data', fontsize=12)
        ax.set_ylabel('Peso (kg)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def show_comparacao_pacientes(self):
        query = """SELECT p.nome, p.peso, p.imc FROM pacientes p ORDER BY p.nome"""
        dados = self.db.execute_query(query)
        
        if not dados:
            QMessageBox.information(self, "Info", "Nenhum paciente cadastrado!")
            return
        
        self.figure.clear()
        
        ax1 = self.figure.add_subplot(121)
        nomes = [d[0][:10] + '...' if len(d[0]) > 10 else d[0] for d in dados]
        pesos = [float(d[1]) for d in dados]
        
        ax1.bar(range(len(nomes)), pesos, color='#A23B72')
        ax1.set_title('Comparação de Peso', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Pacientes', fontsize=12)
        ax1.set_ylabel('Peso (kg)', fontsize=12)
        ax1.set_xticks(range(len(nomes)))
        ax1.set_xticklabels(nomes, rotation=45, ha='right')
        
        ax2 = self.figure.add_subplot(122)
        imcs = [float(d[2]) if d[2] else 0 for d in dados]
        
        colors = ['green' if imc < 25 else 'orange' if imc < 30 else 'red' for imc in imcs]
        ax2.bar(range(len(nomes)), imcs, color=colors)
        ax2.set_title('Comparação de IMC', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Pacientes', fontsize=12)
        ax2.set_ylabel('IMC', fontsize=12)
        ax2.set_xticks(range(len(nomes)))
        ax2.set_xticklabels(nomes, rotation=45, ha='right')
        
        ax2.axhline(y=25, color='orange', linestyle='--', alpha=0.7, label='Sobrepeso')
        ax2.axhline(y=30, color='red', linestyle='--', alpha=0.7, label='Obesidade')
        ax2.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def show_consultas_mes(self):
        query = """SELECT MONTH(data_consulta) as mes, COUNT(*) as total 
                  FROM consultas WHERE YEAR(data_consulta) = YEAR(CURDATE())
                  GROUP BY MONTH(data_consulta) ORDER BY mes"""
        dados = self.db.execute_query(query)
        
        if not dados:
            QMessageBox.information(self, "Info", "Nenhuma consulta cadastrada este ano!")
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        mes_dados = [0] * 12
        for d in dados:
            mes_dados[d[0] - 1] = d[1]
        
        ax.bar(meses, mes_dados, color='#F18F01')
        ax.set_title('Consultas por Mês - ' + str(datetime.now().year), fontsize=14, fontweight='bold')
        ax.set_xlabel('Mês', fontsize=12)
        ax.set_ylabel('Número de Consultas', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        for i, v in enumerate(mes_dados):
            if v > 0:
                ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
        self.figure.tight_layout()
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Sistema de Nutricionista - v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        self.create_pacientes_tab()
        self.create_consultas_tab()
        self.create_dietas_tab()
        self.create_graficos_tab()
        self.create_financeiro_tab()
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        self.statusBar().showMessage("Sistema pronto - Conectado ao banco de dados")
        self.statusBar().setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

    def backup_dados(self):
        try:
            import subprocess
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_nutricionista_{timestamp}.sql"
            
            backup_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Backup", 
                backup_filename,
                "Arquivos SQL (*.sql);;Todos os Arquivos (*)"
            )
            
            if backup_path:
                cmd = [
                    'mysqldump',
                    '-h', 'localhost',
                    '-u', 'root',
                    '-p',
                    'sistema_nutricionista'
                ]
                
                with open(backup_path, 'w') as backup_file:
                    process = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
                    
                    if process.returncode == 0:
                        QMessageBox.information(self, "Sucesso", f"Backup realizado com sucesso!\nArquivo: {backup_path}")
                    else:
                        QMessageBox.critical(self, "Erro", f"Erro ao realizar backup:\n{process.stderr}")
        
        except Exception as e:
            try:
                backup_path, _ = QFileDialog.getSaveFileName(
                    self, "Salvar Backup (Formato Texto)", 
                    f"backup_dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "Arquivos de Texto (*.txt)"
                )
                
                if backup_path:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write("BACKUP DO SISTEMA NUTRICIONISTA\n")
                        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        f.write("="*50 + "\n\n")
                        
                        f.write("PACIENTES:\n")
                        pacientes = self.db.execute_query("SELECT * FROM pacientes")
                        for p in pacientes:
                            f.write(f"{p}\n")
                        
                        f.write("\nCONSULTAS:\n")
                        consultas = self.db.execute_query("SELECT * FROM consultas")
                        for c in consultas:
                            f.write(f"{c}\n")
                        
                        f.write("\nHISTÓRICO DE PESO:\n")
                        historico = self.db.execute_query("SELECT * FROM historico_peso")
                        for h in historico:
                            f.write(f"{h}\n")
                    
                    QMessageBox.information(self, "Sucesso", f"Backup em formato texto realizado!\nArquivo: {backup_path}")
            
            except Exception as backup_error:
                QMessageBox.critical(self, "Erro", f"Erro ao realizar backup:\n{backup_error}")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('Arquivo')
        
        backup_action = QAction('Backup Dados', self)
        backup_action.triggered.connect(self.backup_dados)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        cadastro_menu = menubar.addMenu('Cadastros')
        
        paciente_action = QAction('Novo Paciente', self)
        paciente_action.setShortcut('Ctrl+N')
        paciente_action.triggered.connect(self.novo_paciente)
        cadastro_menu.addAction(paciente_action)
        
        consulta_action = QAction('Nova Consulta', self)
        consulta_action.setShortcut('Ctrl+Shift+N')
        consulta_action.triggered.connect(self.nova_consulta)
        cadastro_menu.addAction(consulta_action)
        
        relatorio_menu = menubar.addMenu('Relatórios')
        
        rel_pacientes_action = QAction('Relatório de Pacientes', self)
        rel_pacientes_action.triggered.connect(self.relatorio_pacientes)
        relatorio_menu.addAction(rel_pacientes_action)
        
        rel_financeiro_action = QAction('Relatório Financeiro', self)
        rel_financeiro_action.triggered.connect(self.relatorio_financeiro)
        relatorio_menu.addAction(rel_financeiro_action)
        
        help_menu = menubar.addMenu('Ajuda')
        
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.sobre)
        help_menu.addAction(about_action)
    
    def create_pacientes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        btn_novo = QPushButton("➕ Novo Paciente")
        btn_editar = QPushButton("✏️ Editar")
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_atualizar = QPushButton("🔄 Atualizar")
        
        btn_novo.clicked.connect(self.novo_paciente)
        btn_editar.clicked.connect(self.editar_paciente)
        btn_excluir.clicked.connect(self.excluir_paciente)
        btn_atualizar.clicked.connect(self.atualizar_pacientes)
        
        toolbar.addWidget(btn_novo)
        toolbar.addWidget(btn_editar)
        toolbar.addWidget(btn_excluir)
        toolbar.addWidget(btn_atualizar)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("🔍 Filtros:"))
        
        self.filter_nome = QLineEdit()
        self.filter_nome.setPlaceholderText("Buscar por nome...")
        
        self.filter_idade_min = QSpinBox()
        self.filter_idade_min.setRange(0, 120)
        self.filter_idade_max = QSpinBox()
        self.filter_idade_max.setRange(0, 120)
        self.filter_idade_max.setValue(120)
        
        filter_layout.addWidget(QLabel("Nome:"))
        filter_layout.addWidget(self.filter_nome)
        filter_layout.addWidget(QLabel("Idade:"))
        filter_layout.addWidget(self.filter_idade_min)
        filter_layout.addWidget(QLabel("até"))
        filter_layout.addWidget(self.filter_idade_max)
        
        btn_filtrar = QPushButton("🔍 Filtrar")
        btn_limpar = QPushButton("🧹 Limpar")
        btn_filtrar.clicked.connect(self.filtrar_pacientes)
        btn_limpar.clicked.connect(self.limpar_filtros)
        filter_layout.addWidget(btn_filtrar)
        filter_layout.addWidget(btn_limpar)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        self.table_pacientes = QTableWidget()
        self.table_pacientes.setColumnCount(8)
        self.table_pacientes.setHorizontalHeaderLabels([
            "ID", "Nome", "Idade", "Sexo", "Peso", "Altura", "IMC", "Telefone"
        ])
        
        header = self.table_pacientes.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_pacientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_pacientes.setAlternatingRowColors(True)
        self.table_pacientes.setSortingEnabled(True)
        layout.addWidget(self.table_pacientes)
        
        self.lbl_total_pacientes = QLabel("Total de pacientes: 0")
        layout.addWidget(self.lbl_total_pacientes)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "👥 Pacientes")
        
        self.atualizar_pacientes()
    
    def create_consultas_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        
        btn_nova = QPushButton("➕ Nova Consulta")
        btn_editar = QPushButton("✏️ Editar")
        btn_excluir = QPushButton("🗑️ Excluir")
        btn_atualizar = QPushButton("🔄 Atualizar")
        
        btn_nova.clicked.connect(self.nova_consulta)
        btn_editar.clicked.connect(self.editar_consulta)
        btn_excluir.clicked.connect(self.excluir_consulta)
        btn_atualizar.clicked.connect(self.atualizar_consultas)
        
        toolbar.addWidget(btn_nova)
        toolbar.addWidget(btn_editar)
        toolbar.addWidget(btn_excluir)
        toolbar.addWidget(btn_atualizar)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        filter_consulta_layout = QHBoxLayout()
        filter_consulta_layout.addWidget(QLabel("🔍 Filtros:"))
        
        self.filter_status = QComboBox()
        self.filter_status.addItems(['Todos', 'Agendada', 'Realizada', 'Cancelada'])
        
        self.filter_data_inicio = QDateEdit()
        self.filter_data_inicio.setDate(QDate.currentDate().addDays(-30))
        self.filter_data_fim = QDateEdit()
        self.filter_data_fim.setDate(QDate.currentDate().addDays(30))
        
        filter_consulta_layout.addWidget(QLabel("Status:"))
        filter_consulta_layout.addWidget(self.filter_status)
        filter_consulta_layout.addWidget(QLabel("De:"))
        filter_consulta_layout.addWidget(self.filter_data_inicio)
        filter_consulta_layout.addWidget(QLabel("Até:"))
        filter_consulta_layout.addWidget(self.filter_data_fim)
        
        btn_filtrar_consulta = QPushButton("🔍 Filtrar")
        btn_filtrar_consulta.clicked.connect(self.filtrar_consultas)
        filter_consulta_layout.addWidget(btn_filtrar_consulta)
        filter_consulta_layout.addStretch()
        
        layout.addLayout(filter_consulta_layout)
        
        self.table_consultas = QTableWidget()
        self.table_consultas.setColumnCount(6)
        self.table_consultas.setHorizontalHeaderLabels([
            "ID", "Paciente", "Data/Hora", "Status", "Valor", "Peso Atual"
        ])
        
        header = self.table_consultas.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_consultas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_consultas.setAlternatingRowColors(True)
        self.table_consultas.setSortingEnabled(True)
        layout.addWidget(self.table_consultas)
        
        self.lbl_total_consultas = QLabel("Total de consultas: 0")
        layout.addWidget(self.lbl_total_consultas)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "📅 Consultas")
        
        self.atualizar_consultas()
    
    def create_dietas_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Planos Alimentares")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        toolbar = QHBoxLayout()
        btn_novo_plano = QPushButton("➕ Novo Plano")
        btn_templates = QPushButton("📝 Templates")
        btn_calcular_calorias = QPushButton("🧮 Calcular Calorias")
        
        btn_novo_plano.clicked.connect(self.novo_plano_alimentar)
        btn_templates.clicked.connect(self.gerenciar_templates)
        btn_calcular_calorias.clicked.connect(self.calcular_calorias)
        
        toolbar.addWidget(btn_novo_plano)
        toolbar.addWidget(btn_templates)
        toolbar.addWidget(btn_calcular_calorias)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("Planos Alimentares:"))
        self.list_planos = QListWidget()
        self.list_planos.itemClicked.connect(self.carregar_plano_selecionado)
        left_layout.addWidget(self.list_planos)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        self.plano_details = QTextEdit()
        self.plano_details.setPlaceholderText("Selecione um plano para visualizar os detalhes...")
        right_layout.addWidget(QLabel("Detalhes do Plano:"))
        right_layout.addWidget(self.plano_details)
        
        plan_buttons = QHBoxLayout()
        btn_editar_plano = QPushButton("✏️ Editar Plano")
        btn_excluir_plano = QPushButton("🗑️ Excluir Plano")
        btn_imprimir_plano = QPushButton("🖨️ Imprimir")
        
        btn_editar_plano.clicked.connect(self.editar_plano_alimentar)
        btn_excluir_plano.clicked.connect(self.excluir_plano_alimentar)
        btn_imprimir_plano.clicked.connect(self.imprimir_plano)
        
        plan_buttons.addWidget(btn_editar_plano)
        plan_buttons.addWidget(btn_excluir_plano)
        plan_buttons.addWidget(btn_imprimir_plano)
        plan_buttons.addStretch()
        
        right_layout.addLayout(plan_buttons)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "🍎 Dietas")
        
        self.carregar_planos_alimentares()
    
    def create_graficos_tab(self):
        self.graph_widget = GraphWidget(self.db)
        self.tab_widget.addTab(self.graph_widget, "📊 Gráficos")
    
    def create_financeiro_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        resumo_widget = QWidget()
        resumo_widget.setStyleSheet("background-color: #f0f0f0; border-radius: 8px; padding: 16px;")
        resumo_layout = QHBoxLayout()
        
        self.lbl_total_receitas = QLabel("💰 Total Receitas: R$ 0,00")
        self.lbl_total_pendentes = QLabel("⏳ Total Pendente: R$ 0,00")
        self.lbl_mes_atual = QLabel("📅 Mês Atual: R$ 0,00")
        
        self.lbl_total_receitas.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        self.lbl_total_pendentes.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
        self.lbl_mes_atual.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
        
        resumo_layout.addWidget(self.lbl_total_receitas)
        resumo_layout.addWidget(self.lbl_total_pendentes)
        resumo_layout.addWidget(self.lbl_mes_atual)
        resumo_layout.addStretch()
        
        resumo_widget.setLayout(resumo_layout)
        layout.addWidget(resumo_widget)
        
        toolbar = QHBoxLayout()
        btn_atualizar_fin = QPushButton("🔄 Atualizar")
        btn_editar_valor = QPushButton("✏️ Editar Valor")
        btn_relatorio_fin = QPushButton("📊 Relatório Mensal")
        btn_exportar = QPushButton("💾 Exportar")
        
        btn_atualizar_fin.clicked.connect(self.atualizar_financeiro)
        btn_editar_valor.clicked.connect(self.editar_valor_consulta)
        btn_relatorio_fin.clicked.connect(self.relatorio_financeiro)
        btn_exportar.clicked.connect(self.exportar_financeiro)
        
        toolbar.addWidget(btn_atualizar_fin)
        toolbar.addWidget(btn_editar_valor)
        toolbar.addWidget(btn_relatorio_fin)
        toolbar.addWidget(btn_exportar)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.table_financeiro = QTableWidget()
        self.table_financeiro.setColumnCount(7)
        self.table_financeiro.setHorizontalHeaderLabels([
            "Consulta ID", "Paciente", "Valor", "Status", "Data Consulta", "Forma Pagamento", "Observações"
        ])
        
        header = self.table_financeiro.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_financeiro.setAlternatingRowColors(True)
        self.table_financeiro.setSortingEnabled(True)
        layout.addWidget(self.table_financeiro)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "💰 Financeiro")
        
        self.atualizar_financeiro()

    def editar_valor_consulta(self):
        row = self.table_financeiro.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta para editar o valor!")
            return
        
        consulta_id = int(self.table_financeiro.item(row, 0).text())
        valor_atual = self.table_financeiro.item(row, 2).text().replace("R$ ", "").replace(",", ".")
        
        novo_valor, ok = QInputDialog.getDouble(
            self, "Editar Valor", "Novo valor da consulta:", 
            float(valor_atual) if valor_atual else 0.0, 0, 9999, 2
        )
        
        if ok:
            query = "UPDATE consultas SET valor = %s WHERE id = %s"
            self.db.execute_insert(query, (novo_valor, consulta_id))
            self.atualizar_financeiro()
            self.atualizar_consultas()
            self.statusBar().showMessage("✅ Valor atualizado com sucesso!", 3000)
    
    def novo_paciente(self):
        dialog = PacienteDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_pacientes()
            self.statusBar().showMessage("✅ Paciente cadastrado com sucesso!", 3000)
    
    def editar_paciente(self):
        row = self.table_pacientes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente para editar!")
            return
        
        paciente_id = int(self.table_pacientes.item(row, 0).text())
        paciente_data = self.db.execute_query(
            "SELECT * FROM pacientes WHERE id = %s", (paciente_id,)
        )[0]
        
        dialog = PacienteDialog(self.db, paciente_data)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_pacientes()
            self.statusBar().showMessage("✅ Paciente atualizado com sucesso!", 3000)
    
    def excluir_paciente(self):
        row = self.table_pacientes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente para excluir!")
            return
        
        paciente_id = int(self.table_pacientes.item(row, 0).text())
        nome = self.table_pacientes.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o paciente {nome}?\nTodos os dados relacionados serão excluídos!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.execute_insert("DELETE FROM historico_peso WHERE paciente_id = %s", (paciente_id,))
            self.db.execute_insert("DELETE FROM consultas WHERE paciente_id = %s", (paciente_id,))
            self.db.execute_insert("DELETE FROM pacientes WHERE id = %s", (paciente_id,))
            self.atualizar_pacientes()
            self.statusBar().showMessage("✅ Paciente excluído com sucesso!", 3000)
    
    def atualizar_pacientes(self):
        query = """SELECT id, nome, idade, sexo, peso, altura, imc, telefone 
                  FROM pacientes ORDER BY nome"""
        dados = self.db.execute_query(query)
        
        self.table_pacientes.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            for j, value in enumerate(row):
                if j == 6: 
                    value = f"{float(value):.2f}" if value else "0.00"
                elif j in [4, 5]:  
                    value = f"{float(value):.2f}"
                
                item = QTableWidgetItem(str(value))
                if j == 6: 
                    imc = float(value) if value != "0.00" else 0
                    if imc < 18.5:
                        item.setBackground(QColor('#E3F2FD')) 
                    elif imc < 25:
                        item.setBackground(QColor('#E8F5E8'))  
                    elif imc < 30:
                        item.setBackground(QColor('#FFF3E0')) 
                    else:
                        item.setBackground(QColor('#FFEBEE')) 
                
                self.table_pacientes.setItem(i, j, item)
        
        self.lbl_total_pacientes.setText(f"Total de pacientes: {len(dados)}")
    
    def filtrar_pacientes(self):
        nome = self.filter_nome.text().strip()
        idade_min = self.filter_idade_min.value()
        idade_max = self.filter_idade_max.value()
        
        conditions = []
        params = []
        
        if nome:
            conditions.append("nome LIKE %s")
            params.append(f"%{nome}%")
        
        conditions.append("idade BETWEEN %s AND %s")
        params.extend([idade_min, idade_max])
        
        where_clause = " AND ".join(conditions)
        query = f"""SELECT id, nome, idade, sexo, peso, altura, imc, telefone 
                   FROM pacientes WHERE {where_clause} ORDER BY nome"""
        
        dados = self.db.execute_query(query, params)
        
        self.table_pacientes.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            for j, value in enumerate(row):
                if j == 6:  # IMC
                    value = f"{float(value):.2f}" if value else "0.00"
                elif j in [4, 5]:  # Peso e Altura
                    value = f"{float(value):.2f}"
                
                self.table_pacientes.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.lbl_total_pacientes.setText(f"Total de pacientes (filtrado): {len(dados)}")
    
    def limpar_filtros(self):
        self.filter_nome.clear()
        self.filter_idade_min.setValue(0)
        self.filter_idade_max.setValue(120)
        self.atualizar_pacientes()
    
    def nova_consulta(self):
        dialog = ConsultaDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_consultas()
            self.atualizar_financeiro()
            self.statusBar().showMessage("✅ Consulta cadastrada com sucesso!", 3000)
    
    def editar_consulta(self):
        row = self.table_consultas.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta para editar!")
            return
        
        consulta_id = int(self.table_consultas.item(row, 0).text())
        consulta_data = self.db.execute_query(
            "SELECT * FROM consultas WHERE id = %s", (consulta_id,)
        )[0]
        
        dialog = ConsultaDialog(self.db, consulta_data)
        if dialog.exec_() == QDialog.Accepted:
            self.atualizar_consultas()
            self.atualizar_financeiro()
            self.statusBar().showMessage("✅ Consulta atualizada com sucesso!", 3000)
    
    def excluir_consulta(self):
        row = self.table_consultas.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta para excluir!")
            return
        
        consulta_id = int(self.table_consultas.item(row, 0).text())
        paciente_nome = self.table_consultas.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir a consulta do paciente {paciente_nome}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.execute_insert("DELETE FROM consultas WHERE id = %s", (consulta_id,))
            self.atualizar_consultas()
            self.atualizar_financeiro()
            self.statusBar().showMessage("✅ Consulta excluída com sucesso!", 3000)
    
    def atualizar_consultas(self):
        query = """SELECT c.id, p.nome, c.data_consulta, c.status, c.valor, c.peso_atual
                  FROM consultas c
                  JOIN pacientes p ON c.paciente_id = p.id
                  ORDER BY c.data_consulta DESC"""
        dados = self.db.execute_query(query)
        
        self.table_consultas.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            for j, value in enumerate(row):
                if j == 4 and value:  # Valor
                    value = f"R$ {float(value):.2f}"
                elif j == 5 and value:  # Peso atual
                    value = f"{float(value):.2f} kg"
                
                item = QTableWidgetItem(str(value) if value else "")
                
                if j == 3: 
                    if value == 'Realizada':
                        item.setBackground(QColor('#E8F5E8'))
                    elif value == 'Agendada':
                        item.setBackground(QColor('#E3F2FD')) 
                    elif value == 'Cancelada':
                        item.setBackground(QColor('#FFEBEE')) 
                
                self.table_consultas.setItem(i, j, item)
        
        self.lbl_total_consultas.setText(f"Total de consultas: {len(dados)}")
    
    def filtrar_consultas(self):
        status = self.filter_status.currentText()
        data_inicio = self.filter_data_inicio.date().toPyDate()
        data_fim = self.filter_data_fim.date().toPyDate()
        
        conditions = ["DATE(c.data_consulta) BETWEEN %s AND %s"]
        params = [data_inicio, data_fim]
        
        if status != 'Todos':
            conditions.append("c.status = %s")
            params.append(status)
        
        where_clause = " AND ".join(conditions)
        query = f"""SELECT c.id, p.nome, c.data_consulta, c.status, c.valor, c.peso_atual
                   FROM consultas c
                   JOIN pacientes p ON c.paciente_id = p.id
                   WHERE {where_clause}
                   ORDER BY c.data_consulta DESC"""
        
        dados = self.db.execute_query(query, params)
        
        self.table_consultas.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            for j, value in enumerate(row):
                if j == 4 and value:  # Valor
                    value = f"R$ {float(value):.2f}"
                elif j == 5 and value:  # Peso atual
                    value = f"{float(value):.2f} kg"
                
                self.table_consultas.setItem(i, j, QTableWidgetItem(str(value) if value else ""))
        
        self.lbl_total_consultas.setText(f"Total de consultas (filtrado): {len(dados)}")
    
    def atualizar_financeiro(self):
        receitas_query = """SELECT SUM(valor) FROM consultas WHERE status = 'Realizada'"""
        receitas = self.db.execute_query(receitas_query)
        total_receitas = float(receitas[0][0]) if receitas[0][0] else 0
        
        pendentes_query = """SELECT SUM(valor) FROM consultas WHERE status = 'Agendada'"""
        pendentes = self.db.execute_query(pendentes_query)
        total_pendentes = float(pendentes[0][0]) if pendentes[0][0] else 0
        
        mes_atual_query = """SELECT SUM(valor) FROM consultas 
                            WHERE status = 'Realizada' AND MONTH(data_consulta) = MONTH(CURDATE())
                            AND YEAR(data_consulta) = YEAR(CURDATE())"""
        mes_atual = self.db.execute_query(mes_atual_query)
        total_mes = float(mes_atual[0][0]) if mes_atual[0][0] else 0
        
        self.lbl_total_receitas.setText(f"💰 Total Receitas: R$ {total_receitas:.2f}")
        self.lbl_total_pendentes.setText(f"⏳ Total Pendente: R$ {total_pendentes:.2f}")
        self.lbl_mes_atual.setText(f"📅 Mês Atual: R$ {total_mes:.2f}")
        
        query = """SELECT c.id, p.nome, c.valor, c.status, c.data_consulta, 
                         'Dinheiro' as forma_pagamento, c.anotacoes
                  FROM consultas c
                  JOIN pacientes p ON c.paciente_id = p.id
                  ORDER BY c.data_consulta DESC"""
        dados = self.db.execute_query(query)
        
        self.table_financeiro.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            for j, value in enumerate(row):
                if j == 2 and value:  # Valor
                    value = f"R$ {float(value):.2f}"
                
                item = QTableWidgetItem(str(value) if value else "")
                
                if j == 3: 
                    if value == 'Realizada':
                        item.setBackground(QColor('#E8F5E8')) 
                    elif value == 'Agendada':
                        item.setBackground(QColor('#FFF3E0'))
                
                self.table_financeiro.setItem(i, j, item)
    
    def novo_plano_alimentar(self):
        dialog = PlanoAlimentarDialog(self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_planos_alimentares()
            self.statusBar().showMessage("✅ Plano alimentar criado com sucesso!", 3000)
    
    def editar_plano_alimentar(self):
        current_item = self.list_planos.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um plano para editar!")
            return
        
        plano_id = current_item.data(Qt.UserRole)
        
        query = """SELECT * FROM planos_alimentares WHERE id = %s"""
        plano_data = self.db.execute_query(query, (plano_id,))
        
        if not plano_data:
            QMessageBox.warning(self, "Erro", "Plano não encontrado!")
            return
        
        dialog = PlanoAlimentarDialog(self.db, plano_data[0])
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_planos_alimentares()
            self.statusBar().showMessage("✅ Plano alimentar atualizado com sucesso!", 3000)

    
    def excluir_plano_alimentar(self):
        current_item = self.list_planos.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um plano para excluir!")
            return
        
        plano_id = current_item.data(Qt.UserRole)
        plano_nome = current_item.text()
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o plano:\n{plano_nome}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            query = "DELETE FROM planos_alimentares WHERE id = %s"
            result = self.db.execute_insert(query, (plano_id,))
            
            if result is not None:
                self.carregar_planos_alimentares()
                self.plano_details.clear()
                self.statusBar().showMessage("✅ Plano alimentar excluído com sucesso!", 3000)
            else:
                QMessageBox.critical(self, "Erro", "Erro ao excluir plano alimentar!")

        
    def carregar_planos_alimentares(self):
        query = """SELECT pa.id, pa.titulo, p.nome, pa.objetivo, pa.status
                FROM planos_alimentares pa
                JOIN pacientes p ON pa.paciente_id = p.id
                ORDER BY pa.data_criacao DESC"""
        
        planos = self.db.execute_query(query)
        self.list_planos.clear()
        
        for plano in planos:
            item_text = f"{plano[1]} - {plano[2]} ({plano[3]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, plano[0]) 
            
            if plano[4] == 'Ativo':
                item.setBackground(QColor('#E8F5E8'))
            elif plano[4] == 'Inativo':
                item.setBackground(QColor('#FFF3E0'))
            else:  
                item.setBackground(QColor('#F5F5F5'))
            
            self.list_planos.addItem(item)

    def carregar_plano_selecionado(self, item):
        plano_id = item.data(Qt.UserRole)
        if not plano_id:
            return
        
        query = """SELECT pa.*, p.nome as paciente_nome
                FROM planos_alimentares pa
                JOIN pacientes p ON pa.paciente_id = p.id
                WHERE pa.id = %s"""
        
        plano_data = self.db.execute_query(query, (plano_id,))
        
        if not plano_data:
            return
        
        plano = plano_data[0]
        
        detalhes = f"""
    PLANO ALIMENTAR: {plano[2]}
    PACIENTE: {plano[15]}
    OBJETIVO: {plano[3]}
    CALORIAS DIÁRIAS: {plano[4]} kcal
    PREFERÊNCIA: {plano[5]}
    STATUS: {plano[14]}

    DETALHES DA PREFERÊNCIA:
    {plano[6] if plano[6] else 'Nenhuma observação especial'}

    CAFÉ DA MANHÃ:
    {plano[7] if plano[7] else 'Não especificado'}

    LANCHE DA MANHÃ:
    {plano[8] if plano[8] else 'Não especificado'}

    ALMOÇO:
    {plano[9] if plano[9] else 'Não especificado'}

    LANCHE DA TARDE:
    {plano[10] if plano[10] else 'Não especificado'}

    JANTAR:
    {plano[11] if plano[11] else 'Não especificado'}

    CEIA:
    {plano[12] if plano[12] else 'Não especificado'}

    OBSERVAÇÕES GERAIS:
    {plano[13] if plano[13] else 'Nenhuma observação adicional'}

    Data de Criação: {plano[14]}
        """
        
        self.plano_details.setPlainText(detalhes)

        
    def gerenciar_templates(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Gerenciar Templates de Dietas")
        dialog.setFixedSize(800, 600)
        
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        btn_novo_template = QPushButton("➕ Novo Template")
        btn_editar_template = QPushButton("✏️ Editar")
        btn_excluir_template = QPushButton("🗑️ Excluir")
        btn_aplicar_template = QPushButton("📋 Aplicar a Paciente")
        
        toolbar.addWidget(btn_novo_template)
        toolbar.addWidget(btn_editar_template)
        toolbar.addWidget(btn_excluir_template)
        toolbar.addWidget(btn_aplicar_template)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        templates_list = QListWidget()
        
        templates_predefinidos = [
            "Template Emagrecimento Básico",
            "Template Ganho de Massa",
            "Template Diabetes",
            "Template Hipertensão",
            "Template Vegetariano",
            "Template Low Carb"
        ]
        
        for template in templates_predefinidos:
            item = QListWidgetItem(template)
            item.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            templates_list.addItem(item)
        
        layout.addWidget(QLabel("Templates Disponíveis:"))
        layout.addWidget(templates_list)
        
        preview_area = QTextEdit()
        preview_area.setPlaceholderText("Selecione um template para visualizar...")
        layout.addWidget(QLabel("Preview do Template:"))
        layout.addWidget(preview_area)
        
        def mostrar_preview():
            current_item = templates_list.currentItem()
            if current_item:
                template_name = current_item.text()
                preview_content = self.get_template_content(template_name)
                preview_area.setPlainText(preview_content)
        
        def aplicar_template():
            current_item = templates_list.currentItem()
            if not current_item:
                QMessageBox.warning(dialog, "Aviso", "Selecione um template!")
                return
            
            pacientes = self.db.execute_query("SELECT id, nome FROM pacientes ORDER BY nome")
            if not pacientes:
                QMessageBox.information(dialog, "Info", "Nenhum paciente cadastrado!")
                return
            
            items = [f"{p[1]}" for p in pacientes]
            item, ok = QInputDialog.getItem(dialog, "Selecionar Paciente", "Aplicar template para:", items, 0, False)
            
            if ok and item:
                template_dialog = PlanoAlimentarDialog(self.db)
                template_dialog.titulo.setText(f"{current_item.text()} - {item}")
                
                template_content = self.get_template_content(current_item.text())
                template_dialog.observacoes.setPlainText(template_content)
                
                if template_dialog.exec_() == QDialog.Accepted:
                    self.carregar_planos_alimentares()
                    QMessageBox.information(dialog, "Sucesso", "Template aplicado com sucesso!")
        
        templates_list.itemClicked.connect(lambda: mostrar_preview())
        btn_aplicar_template.clicked.connect(aplicar_template)
        btn_novo_template.clicked.connect(lambda: QMessageBox.information(dialog, "Info", "Funcionalidade de criação de templates personalizada em desenvolvimento!"))
        
        btn_layout = QHBoxLayout()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(dialog.close)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_fechar)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def get_template_content(self, template_name):
        templates = {
            "Template Emagrecimento Básico": """
    CAFÉ DA MANHÃ:
    - 1 xícara de café com leite desnatado (sem açúcar)
    - 2 fatias de pão integral
    - 1 colher de chá de geleia diet
    - 1 fruta pequena

    LANCHE DA MANHÃ:
    - 1 iogurte natural desnatado
    - 1 colher de sopa de granola

    ALMOÇO:
    - Salada verde à vontade (alface, rúcula, tomate)
    - 120g de proteína magra (frango, peixe, carne magra)
    - 3 colheres de sopa de arroz integral
    - 2 colheres de sopa de feijão
    - Legumes refogados (abobrinha, cenoura, vagem)

    LANCHE DA TARDE:
    - 1 fruta média
    - 10 castanhas ou amêndoas

    JANTAR:
    - Sopa de legumes (sem batata)
    - 100g de proteína grelhada
    - Salada verde com azeite (1 colher de chá)

    CEIA:
    - 1 copo de leite desnatado
    - 2 biscoitos integrais

    OBSERVAÇÕES:
    - Beber 2-3 litros de água por dia
    - Evitar açúcar, doces e frituras
    - Fazer exercícios 3x por semana
    - Calorias aproximadas: 1200-1400 kcal/dia
            """,
            
            "Template Ganho de Massa": """
    CAFÉ DA MANHÃ:
    - 1 copo de leite integral
    - 3 fatias de pão integral com requeijão
    - 1 banana com aveia
    - 2 ovos mexidos

    LANCHE DA MANHÃ:
    - Vitamina: 1 copo de leite + 1 banana + 2 colheres de whey protein
    - 1 punhado de castanhas

    ALMOÇO:
    - Salada variada com azeite
    - 150g de proteína (frango, carne, peixe)
    - 5 colheres de arroz integral
    - 3 colheres de feijão
    - Batata doce assada (100g)

    LANCHE DA TARDE:
    - Sanduíche: 2 fatias de pão integral + peito de peru + queijo
    - 1 fruta
    - Suco natural

    JANTAR:
    - 120g de proteína
    - 4 colheres de arroz ou macarrão integral
    - Legumes refogados
    - Salada verde

    CEIA:
    - 1 copo de leite com achocolatado
    - 3 biscoitos integrais
    - 1 fruta

    OBSERVAÇÕES:
    - Beber bastante água
    - Treinar com regularidade
    - Calorias aproximadas: 2500-3000 kcal/dia
            """,
            
            "Template Diabetes": """
    CAFÉ DA MANHÃ:
    - 1 xícara de café sem açúcar
    - 2 fatias de pão integral
    - 1 fatia de queijo branco
    - 1 fruta (maçã ou pera)

    LANCHE DA MANHÃ:
    - 1 iogurte natural sem açúcar
    - 1 colher de sopa de aveia

    ALMOÇO:
    - Salada verde abundante
    - 120g de proteína magra
    - 3 colheres de arroz integral
    - 2 colheres de feijão
    - Legumes cozidos

    LANCHE DA TARDE:
    - 1 fruta pequena
    - 5 castanhas

    JANTAR:
    - Sopa de legumes (sem batata)
    - 100g de peixe grelhado
    - Salada verde

    CEIA:
    - 1 copo de leite desnatado
    - 1 biscoito integral

    OBSERVAÇÕES:
    - Evitar açúcar e doces
    - Preferir carboidratos integrais
    - Fazer refeições regulares
    - Monitorar glicemia
    - Calorias controladas: 1400-1600 kcal/dia
            """,
            
            "Template Hipertensão": """
    CAFÉ DA MANHÃ:
    - Chá verde ou café (sem açúcar)
    - 2 fatias de pão integral
    - 1 colher de pasta de amendoim natural
    - 1 banana

    LANCHE DA MANHÃ:
    - 1 iogurte natural
    - Frutas vermelhas

    ALMOÇO:
    - Salada verde com azeite extra virgem
    - 120g de peixe ou frango (sem sal)
    - 3 colheres de quinoa ou arroz integral
    - Legumes no vapor

    LANCHE DA TARDE:
    - 1 maçã
    - 1 punhado de nozes

    JANTAR:
    - Sopa de legumes (baixo sódio)
    - 100g de proteína grelhada (temperos naturais)
    - Salada de folhas verdes

    CEIA:
    - Chá de camomila
    - 1 fruta pequena

    OBSERVAÇÕES:
    - Reduzir drasticamente o sal
    - Usar temperos naturais (alho, cebola, ervas)
    - Evitar alimentos processados
    - Aumentar potássio (frutas, vegetais)
    - Calorias: 1500-1800 kcal/dia
            """,
            
            "Template Vegetariano": """
    CAFÉ DA MANHÃ:
    - 1 copo de leite vegetal (aveia, amêndoa)
    - 2 fatias de pão integral
    - 1 colher de pasta de amendoim
    - 1 fruta

    LANCHE DA MANHÃ:
    - Smoothie: frutas + leite vegetal + chia
    - 1 punhado de castanhas

    ALMOÇO:
    - Salada variada com grão-de-bico
    - Quinoa com legumes
    - 2 ovos ou tofu grelhado
    - Feijão ou lentilha

    LANCHE DA TARDE:
    - Hummus com cenoura
    - 1 fruta

    JANTAR:
    - Sopa de legumes com grãos
    - Omelete de vegetais
    - Salada verde

    CEIA:
    - Leite vegetal morno
    - 1 fruta seca

    OBSERVAÇÕES:
    - Combinar proteínas vegetais
    - Suplementar B12 se necessário
    - Variar grãos e leguminosas
    - Incluir ferro (folhas verdes escuras)
    - Calorias: 1600-2000 kcal/dia
            """,
            
            "Template Low Carb": """
    CAFÉ DA MANHÃ:
    - Ovos mexidos com queijo
    - Abacate com azeite
    - Café com creme de leite

    LANCHE DA MANHÃ:
    - Castanhas variadas
    - Queijo

    ALMOÇO:
    - Salada verde abundante
    - 150g de carne ou peixe
    - Legumes refogados (brócolis, couve-flor)
    - Azeite extra virgem

    LANCHE DA TARDE:
    - Azeitonas
    - Fatias de pepino com cream cheese

    JANTAR:
    - 120g de proteína
    - Salada de folhas verdes
    - Aspargos grelhados

    CEIA:
    - Chá verde
    - 1 punhado de nozes

    OBSERVAÇÕES:
    - Máximo 50g de carboidratos/dia
    - Priorizar gorduras boas
    - Evitar açúcar e grãos
    - Beber muita água
    - Calorias: 1400-1800 kcal/dia
            """
        }
        
        return templates.get(template_name, "Template não encontrado.")

    def calcular_calorias(self):
        dialog = CalculadoraCaloriasDialog(self.db)
        dialog.exec_()

    def imprimir_plano(self):
        current_item = self.list_planos.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione um plano para imprimir!")
            return
        
        plano_id = current_item.data(Qt.UserRole)
        if not plano_id:
            QMessageBox.warning(self, "Aviso", "Plano inválido!")
            return
        
        query = """SELECT pa.*, p.nome as paciente_nome, p.idade, p.peso, p.altura
                FROM planos_alimentares pa
                JOIN pacientes p ON pa.paciente_id = p.id
                WHERE pa.id = %s"""
        
        plano_data = self.db.execute_query(query, (plano_id,))
        
        if not plano_data:
            QMessageBox.warning(self, "Erro", "Dados do plano não encontrados!")
            return
        
        plano = plano_data[0]
        
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtGui import QTextDocument, QFont
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
                    .patient-info {{ background-color: #f0f0f0; padding: 10px; margin: 10px 0; }}
                    .meal {{ margin: 15px 0; }}
                    .meal-title {{ font-weight: bold; color: #4CAF50; font-size: 14px; }}
                    .meal-content {{ margin-left: 20px; }}
                    .footer {{ margin-top: 30px; text-align: center; font-size: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>PLANO ALIMENTAR</h1>
                    <h2>{plano[2]}</h2>
                </div>
                
                <div class="patient-info">
                    <strong>Paciente:</strong> {plano[16]}<br>
                    <strong>Idade:</strong> {plano[17]} anos<br>
                    <strong>Peso:</strong> {plano[18]} kg<br>
                    <strong>Altura:</strong> {plano[19]} m<br>
                    <strong>Objetivo:</strong> {plano[3]}<br>
                    <strong>Calorias Diárias:</strong> {plano[4]} kcal<br>
                    <strong>Data de Criação:</strong> {plano[13].strftime('%d/%m/%Y') if plano[13] else 'N/A'}
                </div>
                
                <div class="meal">
                    <div class="meal-title">CAFÉ DA MANHÃ</div>
                    <div class="meal-content">{plano[7] if plano[7] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">LANCHE DA MANHÃ</div>
                    <div class="meal-content">{plano[8] if plano[8] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">ALMOÇO</div>
                    <div class="meal-content">{plano[9] if plano[9] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">LANCHE DA TARDE</div>
                    <div class="meal-content">{plano[10] if plano[10] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">JANTAR</div>
                    <div class="meal-content">{plano[11] if plano[11] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">CEIA</div>
                    <div class="meal-content">{plano[12] if plano[12] else 'Não especificado'}</div>
                </div>
                
                <div class="meal">
                    <div class="meal-title">OBSERVAÇÕES GERAIS</div>
                    <div class="meal-content">{plano[13] if plano[13] else 'Nenhuma observação adicional'}</div>
                </div>
                
                <div class="footer">
                    <p>Sistema de Nutricionista v1.0 - Plano gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </body>
            </html>
            """
            
            document = QTextDocument()
            document.setHtml(html_content)
            document.print_(printer)
            
            QMessageBox.information(self, "Sucesso", "Plano enviado para impressão!")
        
    def relatorio_pacientes(self):
        query = """
        SELECT 
            p.id,
            p.nome,
            p.idade,
            p.sexo,
            p.peso,
            p.altura,
            p.imc,
            p.telefone,
            p.email,
            COUNT(c.id) as total_consultas,
            MAX(c.data_consulta) as ultima_consulta
        FROM pacientes p
        LEFT JOIN consultas c ON p.id = c.paciente_id
        GROUP BY p.id
        ORDER BY p.nome
        """
        
        dados = self.db.execute_query(query)
        
        if not dados:
            QMessageBox.information(self, "Info", "Nenhum paciente cadastrado!")
            return
        
        relatorio_window = QDialog(self)
        relatorio_window.setWindowTitle("Relatório de Pacientes")
        relatorio_window.setFixedSize(1000, 700)
        
        layout = QVBoxLayout()
        
        header = QLabel("RELATÓRIO DE PACIENTES")
        header.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center; margin: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        total_pacientes = len(dados)
        idade_media = sum(d[2] for d in dados) / total_pacientes
        peso_medio = sum(float(d[4]) for d in dados) / total_pacientes
        imc_medio = sum(float(d[6]) if d[6] else 0 for d in dados) / total_pacientes
        
        stats_text = f"""
    ESTATÍSTICAS GERAIS:
    • Total de Pacientes: {total_pacientes}
    • Idade Média: {idade_media:.1f} anos
    • Peso Médio: {peso_medio:.1f} kg
    • IMC Médio: {imc_medio:.1f}
        """
        
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(stats_label)
        
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Nome", "Idade", "Sexo", "Peso", "IMC", "Telefone", "Total Consultas", "Última Consulta"
        ])
        table.setRowCount(len(dados))
        
        for i, row in enumerate(dados):
            table.setItem(i, 0, QTableWidgetItem(str(row[1])))  # Nome
            table.setItem(i, 1, QTableWidgetItem(str(row[2])))  # Idade
            table.setItem(i, 2, QTableWidgetItem(str(row[3])))  # Sexo
            table.setItem(i, 3, QTableWidgetItem(f"{float(row[4]):.1f} kg"))  # Peso
            
            imc_item = QTableWidgetItem(f"{float(row[6]):.1f}" if row[6] else "0.0")
            imc = float(row[6]) if row[6] else 0
            if imc < 18.5:
                imc_item.setBackground(QColor('#E3F2FD'))
            elif imc < 25:
                imc_item.setBackground(QColor('#E8F5E8'))
            elif imc < 30:
                imc_item.setBackground(QColor('#FFF3E0'))
            else:
                imc_item.setBackground(QColor('#FFEBEE'))
            table.setItem(i, 4, imc_item)
            
            table.setItem(i, 5, QTableWidgetItem(str(row[7]) if row[7] else ""))  # Telefone
            table.setItem(i, 6, QTableWidgetItem(str(row[9])))  # Total consultas
            table.setItem(i, 7, QTableWidgetItem(str(row[10]) if row[10] else "Nunca"))  # Última consulta
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn_layout = QHBoxLayout()
        btn_exportar_pac = QPushButton("💾 Exportar")
        btn_fechar = QPushButton("Fechar")
        
        btn_exportar_pac.clicked.connect(lambda: self.exportar_relatorio_pacientes(dados))
        btn_fechar.clicked.connect(relatorio_window.close)
        
        btn_layout.addWidget(btn_exportar_pac)
        btn_layout.addWidget(btn_fechar)
        layout.addLayout(btn_layout)
        
        relatorio_window.setLayout(layout)
        relatorio_window.exec_()

        
    def relatorio_financeiro(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Relatório Financeiro")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        mes_combo = QComboBox()
        mes_combo.addItems(['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'])
        mes_combo.setCurrentIndex(datetime.now().month - 1)
        
        ano_spin = QSpinBox()
        ano_spin.setRange(2020, 2030)
        ano_spin.setValue(datetime.now().year)
        
        form_layout.addRow("Mês:", mes_combo)
        form_layout.addRow("Ano:", ano_spin)
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        btn_gerar = QPushButton("Gerar Relatório")
        btn_cancelar = QPushButton("Cancelar")
        
        button_layout.addWidget(btn_gerar)
        button_layout.addWidget(btn_cancelar)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def gerar_relatorio():
            mes = mes_combo.currentIndex() + 1
            ano = ano_spin.value()
            
            query = """
            SELECT 
                c.id,
                p.nome,
                c.data_consulta,
                c.valor,
                c.status
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE MONTH(c.data_consulta) = %s AND YEAR(c.data_consulta) = %s
            ORDER BY c.data_consulta
            """
            
            dados = self.db.execute_query(query, (mes, ano))
            
            if not dados:
                QMessageBox.information(self, "Info", f"Nenhuma consulta encontrada para {mes_combo.currentText()}/{ano}")
                return
            
            total_geral = sum(float(d[3]) if d[3] else 0 for d in dados)
            total_realizada = sum(float(d[3]) if d[3] and d[4] == 'Realizada' else 0 for d in dados)
            total_pendente = sum(float(d[3]) if d[3] and d[4] == 'Agendada' else 0 for d in dados)
            
            relatorio_window = QDialog(self)
            relatorio_window.setWindowTitle(f"Relatório Financeiro - {mes_combo.currentText()}/{ano}")
            relatorio_window.setFixedSize(800, 600)
            
            layout_rel = QVBoxLayout()
            
            header = QLabel(f"RELATÓRIO FINANCEIRO - {mes_combo.currentText().upper()}/{ano}")
            header.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center; margin: 10px;")
            header.setAlignment(Qt.AlignCenter)
            layout_rel.addWidget(header)
            
            resumo_text = f"""
    RESUMO FINANCEIRO:
    • Total de Consultas: {len(dados)}
    • Total Arrecadado (Realizadas): R$ {total_realizada:.2f}
    • Total Pendente (Agendadas): R$ {total_pendente:.2f}
    • Total Geral: R$ {total_geral:.2f}

    DETALHAMENTO:
            """
            
            resumo_label = QLabel(resumo_text)
            resumo_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
            layout_rel.addWidget(resumo_label)
            
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["ID", "Paciente", "Data", "Valor", "Status"])
            table.setRowCount(len(dados))
            
            for i, row in enumerate(dados):
                table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                table.setItem(i, 2, QTableWidgetItem(str(row[2])))
                table.setItem(i, 3, QTableWidgetItem(f"R$ {float(row[3]):.2f}" if row[3] else "R$ 0,00"))
                
                status_item = QTableWidgetItem(str(row[4]))
                if row[4] == 'Realizada':
                    status_item.setBackground(QColor('#E8F5E8'))
                elif row[4] == 'Agendada':
                    status_item.setBackground(QColor('#FFF3E0'))
                table.setItem(i, 4, status_item)
            
            table.resizeColumnsToContents()
            layout_rel.addWidget(table)
            
            btn_layout = QHBoxLayout()
            btn_imprimir = QPushButton("🖨️ Imprimir")
            btn_salvar = QPushButton("💾 Salvar PDF")
            btn_fechar = QPushButton("Fechar")
            
            btn_imprimir.clicked.connect(lambda: QMessageBox.information(relatorio_window, "Info", "Funcionalidade de impressão em desenvolvimento"))
            btn_salvar.clicked.connect(lambda: self.salvar_relatorio_pdf(dados, mes_combo.currentText(), ano, total_realizada, total_pendente, total_geral))
            btn_fechar.clicked.connect(relatorio_window.close)
            
            btn_layout.addWidget(btn_imprimir)
            btn_layout.addWidget(btn_salvar)
            btn_layout.addWidget(btn_fechar)
            layout_rel.addLayout(btn_layout)
            
            relatorio_window.setLayout(layout_rel)
            relatorio_window.exec_()
            dialog.close()
        
        btn_gerar.clicked.connect(gerar_relatorio)
        btn_cancelar.clicked.connect(dialog.close)
        
        dialog.exec_()
    
    def exportar_financeiro(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Exportar Dados Financeiros")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        periodo_group = QGroupBox("Período")
        periodo_layout = QVBoxLayout()
        
        self.radio_mes_atual = QRadioButton("Mês Atual")
        self.radio_ano_atual = QRadioButton("Ano Atual")
        self.radio_todos = QRadioButton("Todos os Dados")
        self.radio_personalizado = QRadioButton("Período Personalizado")
        
        self.radio_mes_atual.setChecked(True)
        
        periodo_layout.addWidget(self.radio_mes_atual)
        periodo_layout.addWidget(self.radio_ano_atual)
        periodo_layout.addWidget(self.radio_todos)
        periodo_layout.addWidget(self.radio_personalizado)
        
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate().addDays(-30))
        self.data_inicio.setEnabled(False)
        
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setEnabled(False)
        
        self.radio_personalizado.toggled.connect(lambda checked: self.data_inicio.setEnabled(checked))
        self.radio_personalizado.toggled.connect(lambda checked: self.data_fim.setEnabled(checked))
        
        periodo_layout.addWidget(QLabel("Data Início:"))
        periodo_layout.addWidget(self.data_inicio)
        periodo_layout.addWidget(QLabel("Data Fim:"))
        periodo_layout.addWidget(self.data_fim)
        
        periodo_group.setLayout(periodo_layout)
        layout.addWidget(periodo_group)
        
        formato_group = QGroupBox("Formato")
        formato_layout = QVBoxLayout()
        
        self.radio_csv = QRadioButton("CSV (Excel)")
        self.radio_txt = QRadioButton("Texto")
        self.radio_csv.setChecked(True)
        
        formato_layout.addWidget(self.radio_csv)
        formato_layout.addWidget(self.radio_txt)
        formato_group.setLayout(formato_layout)
        layout.addWidget(formato_group)
        
        button_layout = QHBoxLayout()
        btn_exportar = QPushButton("Exportar")
        btn_cancelar = QPushButton("Cancelar")
        
        button_layout.addWidget(btn_exportar)
        button_layout.addWidget(btn_cancelar)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def realizar_exportacao():
            if self.radio_mes_atual.isChecked():
                query = """
                SELECT c.id, p.nome, c.data_consulta, c.valor, c.status, c.anotacoes
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE MONTH(c.data_consulta) = MONTH(CURDATE()) 
                AND YEAR(c.data_consulta) = YEAR(CURDATE())
                ORDER BY c.data_consulta
                """
                params = None
                nome_arquivo = f"financeiro_mes_{datetime.now().month}_{datetime.now().year}"
                
            elif self.radio_ano_atual.isChecked():
                query = """
                SELECT c.id, p.nome, c.data_consulta, c.valor, c.status, c.anotacoes
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE YEAR(c.data_consulta) = YEAR(CURDATE())
                ORDER BY c.data_consulta
                """
                params = None
                nome_arquivo = f"financeiro_ano_{datetime.now().year}"
                
            elif self.radio_personalizado.isChecked():
                query = """
                SELECT c.id, p.nome, c.data_consulta, c.valor, c.status, c.anotacoes
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) BETWEEN %s AND %s
                ORDER BY c.data_consulta
                """
                params = (self.data_inicio.date().toPyDate(), self.data_fim.date().toPyDate())
                nome_arquivo = f"financeiro_{self.data_inicio.date().toString('yyyy_MM_dd')}_a_{self.data_fim.date().toString('yyyy_MM_dd')}"
                
            else:  
                query = """
                SELECT c.id, p.nome, c.data_consulta, c.valor, c.status, c.anotacoes
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                ORDER BY c.data_consulta
                """
                params = None
                nome_arquivo = "financeiro_completo"
            
            dados = self.db.execute_query(query, params)
            
            if not dados:
                QMessageBox.information(self, "Info", "Nenhum dado encontrado para o período selecionado!")
                return
            
            if self.radio_csv.isChecked():
                extensao = "csv"
                filtro = "Arquivos CSV (*.csv)"
            else:
                extensao = "txt"
                filtro = "Arquivos de Texto (*.txt)"
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exportar Dados Financeiros",
                f"{nome_arquivo}.{extensao}",
                f"{filtro};;Todos os Arquivos (*)"
            )
            
            if filename:
                try:
                    if self.radio_csv.isChecked():
                        import csv
                        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile, delimiter=';')
                            
                            writer.writerow(['ID', 'Paciente', 'Data Consulta', 'Valor', 'Status', 'Observações'])
                            
                            for row in dados:
                                valor = f"{float(row[3]):.2f}" if row[3] else "0.00"
                                writer.writerow([
                                    row[0],  # ID
                                    row[1],  # Nome paciente
                                    row[2],  # Data consulta
                                    valor,   # Valor
                                    row[4],  # Status
                                    row[5] if row[5] else ""  # Observações
                                ])
                    else:
                        with open(filename, 'w', encoding='utf-8') as txtfile:
                            txtfile.write("EXPORTAÇÃO DE DADOS FINANCEIROS\n")
                            txtfile.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                            txtfile.write("="*80 + "\n\n")
                            
                            txtfile.write(f"{'ID':<5} {'Paciente':<25} {'Data':<12} {'Valor':<12} {'Status':<12} {'Observações'}\n")
                            txtfile.write("-"*80 + "\n")
                            
                            for row in dados:
                                valor = f"R$ {float(row[3]):.2f}" if row[3] else "R$ 0,00"
                                txtfile.write(f"{str(row[0]):<5} {str(row[1])[:24]:<25} {str(row[2])[:11]:<12} {valor:<12} {str(row[4]):<12} {str(row[5])[:20] if row[5] else ''}\n")
                    
                    QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso!\nArquivo: {filename}\nTotal de registros: {len(dados)}")
                    dialog.close()
                    
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao exportar dados:\n{e}")
        
        btn_exportar.clicked.connect(realizar_exportacao)
        btn_cancelar.clicked.connect(dialog.close)
        
        dialog.exec_()

    def backup_dados(self):
        QMessageBox.information(self, "Info", "Realizando backup dos dados...")
    
    def sobre(self):
        QMessageBox.about(self, "Sobre", 
                        "Sistema de Nutricionista v1.0\n\n"
                        "Sistema completo para gestão de consultório nutricional.\n"
                        "Desenvolvido com PyQt5 e MySQL.\n\n"
                        "Funcionalidades:\n"
                        "• Cadastro de pacientes\n"
                        "• Agendamento de consultas\n" 
                        "• Planos alimentares\n"
                        "• Gráficos e relatórios\n"
                        "• Controle financeiro")
        
    def exportar_relatorio_pacientes(self, dados):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar Relatório de Pacientes",
            f"relatorio_pacientes_{datetime.now().strftime('%Y_%m_%d')}.csv",
            "Arquivos CSV (*.csv);;Arquivos de Texto (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile, delimiter=';')
                        writer.writerow(['Nome', 'Idade', 'Sexo', 'Peso', 'Altura', 'IMC', 'Telefone', 'Email', 'Total Consultas', 'Última Consulta'])
                        
                        for row in dados:
                            writer.writerow([
                                row[1], row[2], row[3], f"{float(row[4]):.1f}",
                                f"{float(row[5]):.2f}", f"{float(row[6]):.1f}" if row[6] else "0.0",
                                row[7] if row[7] else "", row[8] if row[8] else "",
                                row[9], row[10] if row[10] else "Nunca"
                            ])
                else:
                    with open(filename, 'w', encoding='utf-8') as txtfile:
                        txtfile.write("RELATÓRIO DE PACIENTES\n")
                        txtfile.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                        txtfile.write("="*80 + "\n\n")
                        
                        for row in dados:
                            txtfile.write(f"Nome: {row[1]}\n")
                            txtfile.write(f"Idade: {row[2]} anos\n")
                            txtfile.write(f"Sexo: {row[3]}\n")
                            txtfile.write(f"Peso: {float(row[4]):.1f} kg\n")
                            txtfile.write(f"IMC: {float(row[6]):.1f}\n" if row[6] else "IMC: 0.0\n")
                            txtfile.write(f"Telefone: {row[7]}\n" if row[7] else "Telefone: -\n")
                            txtfile.write(f"Total de Consultas: {row[9]}\n")
                            txtfile.write(f"Última Consulta: {row[10]}\n" if row[10] else "Última Consulta: Nunca\n")
                            txtfile.write("-"*40 + "\n")
                
                QMessageBox.information(self, "Sucesso", f"Relatório exportado com sucesso!\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar relatório:\n{e}")

    def salvar_relatorio_pdf(self, dados, mes, ano, total_realizada, total_pendente, total_geral):
        from datetime import datetime
        import os
        
        conteudo = f"""
    RELATÓRIO FINANCEIRO - {mes.upper()}/{ano}
    Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

    {'='*50}
    RESUMO FINANCEIRO
    {'='*50}
    Total de Consultas: {len(dados)}
    Total Arrecadado (Realizadas): R$ {total_realizada:.2f}
    Total Pendente (Agendadas): R$ {total_pendente:.2f}
    Total Geral: R$ {total_geral:.2f}

    {'='*50}
    DETALHAMENTO DAS CONSULTAS
    {'='*50}
    """
        
        for row in dados:
            valor = f"R$ {float(row[3]):.2f}" if row[3] else "R$ 0,00"
            conteudo += f"ID: {row[0]} | {row[1]} | {row[2]} | {valor} | {row[4]}\n"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório", 
            f"relatorio_financeiro_{mes}_{ano}.txt",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(conteudo)
                QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{e}")

class PlanoAlimentarDialog(QDialog):
    def __init__(self, db, plano_data=None):
        super().__init__()
        self.db = db
        self.plano_data = plano_data
        self.init_ui()
        
        if plano_data:
            self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("Novo Plano Alimentar" if not self.plano_data else "Editar Plano Alimentar")
        self.setFixedSize(600, 700)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.paciente = QComboBox()
        self.load_pacientes()
        
        self.titulo = QLineEdit()
        self.objetivo = QComboBox()
        self.objetivo.addItems(['Emagrecimento', 'Ganho de Massa', 'Manutenção', 'Diabetes', 'Hipertensão'])
        
        self.calorias_dia = QSpinBox()
        self.calorias_dia.setRange(800, 5000)
        self.calorias_dia.setValue(2000)
        
        form_layout.addRow("Paciente:", self.paciente)
        form_layout.addRow("Título do Plano:", self.titulo)
        form_layout.addRow("Objetivo:", self.objetivo)
        form_layout.addRow("Calorias/dia:", self.calorias_dia)
        
        layout.addLayout(form_layout)

        self.preferencia_tipo = QComboBox()
        self.preferencia_tipo.addItems(['Vegetariano', 'Vegano', 'Sem Glúten', 'Sem Lactose', 'Low Carb', 'Outro'])
        self.preferencia_descricao = QTextEdit()
        self.preferencia_descricao.setPlaceholderText("Descreva detalhes da preferência alimentar...")
        self.preferencia_descricao.setMaximumHeight(80)

        form_layout.addRow("Preferência Alimentar:", self.preferencia_tipo)
        form_layout.addRow("Detalhes da Preferência:", self.preferencia_descricao)
        
        self.tab_refeicoes = QTabWidget()
        
        refeicoes = ['Café da Manhã', 'Lanche Manhã', 'Almoço', 'Lanche Tarde', 'Jantar', 'Ceia']
        self.refeicao_texts = {}
        
        for refeicao in refeicoes:
            tab = QWidget()
            tab_layout = QVBoxLayout()
            
            text_edit = QTextEdit()
            text_edit.setPlaceholderText(f"Digite os alimentos para {refeicao.lower()}...")
            self.refeicao_texts[refeicao] = text_edit
            
            tab_layout.addWidget(text_edit)
            tab.setLayout(tab_layout)
            self.tab_refeicoes.addTab(tab, refeicao)
        
        layout.addWidget(self.tab_refeicoes)
        
        layout.addWidget(QLabel("Observações:"))
        self.observacoes = QTextEdit()
        self.observacoes.setMaximumHeight(100)
        layout.addWidget(self.observacoes)
        
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar Plano")
        self.cancel_btn = QPushButton("Cancelar")
        
        self.save_btn.clicked.connect(self.save_plano)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_pacientes(self):
        pacientes = self.db.execute_query("SELECT id, nome FROM pacientes ORDER BY nome")
        self.paciente.clear()
        for p in pacientes:
            self.paciente.addItem(f"{p[1]}", p[0])
    
    def load_data(self):
        """Carregar dados do plano para edição"""
        if not self.plano_data:
            return
        
        for i in range(self.paciente.count()):
            if self.paciente.itemData(i) == self.plano_data[1]:
                self.paciente.setCurrentIndex(i)
                break
        
        self.titulo.setText(str(self.plano_data[2]))
        self.objetivo.setCurrentText(str(self.plano_data[3]))
        self.calorias_dia.setValue(int(self.plano_data[4]))
        
        if self.plano_data[5]:
            self.preferencia_tipo.setCurrentText(str(self.plano_data[5]))
        
        if self.plano_data[6]:
            self.preferencia_descricao.setPlainText(str(self.plano_data[6]))
        
        refeicoes_campos = [
            ('Café da Manhã', 7),
            ('Lanche Manhã', 8),
            ('Almoço', 9),
            ('Lanche Tarde', 10),
            ('Jantar', 11),
            ('Ceia', 12)
        ]
        
        for refeicao_nome, indice in refeicoes_campos:
            if len(self.plano_data) > indice and self.plano_data[indice]:
                self.refeicao_texts[refeicao_nome].setPlainText(str(self.plano_data[indice]))
        
        if len(self.plano_data) > 13 and self.plano_data[13]:
            self.observacoes.setPlainText(str(self.plano_data[13]))
    
    def save_plano(self):
        if not self.titulo.text():
            QMessageBox.warning(self, "Aviso", "Título do plano é obrigatório!")
            return
        
        if self.paciente.currentData() is None:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente!")
            return
        
        refeicoes_data = {}
        for refeicao, text_edit in self.refeicao_texts.items():
            refeicoes_data[refeicao.lower().replace(' ', '_')] = text_edit.toPlainText()
        
        data = (
            self.paciente.currentData(),
            self.titulo.text(),
            self.objetivo.currentText(),
            self.calorias_dia.value(),
            self.preferencia_tipo.currentText(),
            self.preferencia_descricao.toPlainText(),
            refeicoes_data.get('café_da_manhã', ''),
            refeicoes_data.get('lanche_manhã', ''),
            refeicoes_data.get('almoço', ''),
            refeicoes_data.get('lanche_tarde', ''),
            refeicoes_data.get('jantar', ''),
            refeicoes_data.get('ceia', ''),
            self.observacoes.toPlainText()
        )
        
        if self.plano_data: 
            query = """UPDATE planos_alimentares SET 
                       paciente_id=%s, titulo=%s, objetivo=%s, calorias_dia=%s, 
                       preferencia_tipo=%s, preferencia_descricao=%s, cafe_manha=%s, 
                       lanche_manha=%s, almoco=%s, lanche_tarde=%s, jantar=%s, 
                       ceia=%s, observacoes=%s WHERE id=%s"""
            result = self.db.execute_insert(query, data + (self.plano_data[0],))
        else: 
            query = """INSERT INTO planos_alimentares 
                       (paciente_id, titulo, objetivo, calorias_dia, preferencia_tipo, 
                        preferencia_descricao, cafe_manha, lanche_manha, almoco, 
                        lanche_tarde, jantar, ceia, observacoes) 
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            result = self.db.execute_insert(query, data)
        
        if result is not None:
            QMessageBox.information(self, "Sucesso", "Plano alimentar salvo com sucesso!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Erro ao salvar plano alimentar!")


    def calcular_calorias(self):
        dialog = CalculadoraCaloriasDialog(self.db)
        dialog.exec_()

    def create_agenda_tab(self):
        """Criar aba de agenda avançada"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("📅 Agenda de Consultas")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        toolbar = QHBoxLayout()
        btn_hoje = QPushButton("📅 Hoje")
        btn_semana = QPushButton("📊 Esta Semana")
        btn_mes = QPushButton("🗓️ Este Mês")
        btn_nova_consulta = QPushButton("➕ Nova Consulta")
        
        btn_hoje.clicked.connect(self.mostrar_agenda_hoje)
        btn_semana.clicked.connect(self.mostrar_agenda_semana)
        btn_mes.clicked.connect(self.mostrar_agenda_mes)
        btn_nova_consulta.clicked.connect(self.nova_consulta)
        
        toolbar.addWidget(btn_hoje)
        toolbar.addWidget(btn_semana)
        toolbar.addWidget(btn_mes)
        toolbar.addWidget(btn_nova_consulta)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        from PyQt5.QtWidgets import QCalendarWidget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.data_selecionada)
        layout.addWidget(self.calendar)
        
        self.lista_consultas_dia = QListWidget()
        layout.addWidget(QLabel("Consultas do dia selecionado:"))
        layout.addWidget(self.lista_consultas_dia)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "📅 Agenda")
        
        self.mostrar_agenda_hoje()

    def data_selecionada(self, date):
        """Mostrar consultas da data selecionada"""
        data_str = date.toString("yyyy-MM-dd")
        
        query = """SELECT c.id, p.nome, c.data_consulta, c.status, c.valor
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = %s
                ORDER BY TIME(c.data_consulta)"""
        
        consultas = self.db.execute_query(query, (data_str,))
        
        self.lista_consultas_dia.clear()
        
        if not consultas:
            item = QListWidgetItem("Nenhuma consulta agendada para este dia")
            item.setForeground(QColor('#888888'))
            self.lista_consultas_dia.addItem(item)
            return
        
        for consulta in consultas:
            hora = consulta[2].strftime("%H:%M") if consulta[2] else "00:00"
            texto = f"{hora} - {consulta[1]} - {consulta[3]}"
            if consulta[4]:
                texto += f" - R$ {float(consulta[4]):.2f}"
            
            item = QListWidgetItem(texto)
            
            if consulta[3] == 'Realizada':
                item.setBackground(QColor('#E8F5E8'))
            elif consulta[3] == 'Agendada':
                item.setBackground(QColor('#E3F2FD'))
            else:
                item.setBackground(QColor('#FFEBEE'))
            
            item.setData(Qt.UserRole, consulta[0]) 
            self.lista_consultas_dia.addItem(item)

    def mostrar_agenda_hoje(self):
        """Mostrar agenda de hoje"""
        hoje = QDate.currentDate()
        self.calendar.setSelectedDate(hoje)
        self.data_selecionada(hoje)

    def mostrar_agenda_semana(self):
        """Mostrar resumo da semana"""
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        
        query = """SELECT DATE(c.data_consulta) as data, COUNT(*) as total,
                SUM(CASE WHEN c.status = 'Realizada' THEN 1 ELSE 0 END) as realizadas,
                SUM(CASE WHEN c.status = 'Agendada' THEN 1 ELSE 0 END) as agendadas
                FROM consultas c
                WHERE DATE(c.data_consulta) BETWEEN %s AND %s
                GROUP BY DATE(c.data_consulta)
                ORDER BY DATE(c.data_consulta)"""
        
        dados = self.db.execute_query(query, (inicio_semana, fim_semana))
        
        resumo = f"RESUMO DA SEMANA ({inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m/%Y')})\n\n"
        
        if not dados:
            resumo += "Nenhuma consulta agendada para esta semana."
        else:
            for linha in dados:
                data_formatada = linha[0].strftime('%d/%m (%A)')
                resumo += f"{data_formatada}: {linha[1]} consultas ({linha[2]} realizadas, {linha[3]} agendadas)\n"
        
        QMessageBox.information(self, "Agenda da Semana", resumo)

    def mostrar_agenda_mes(self):
        """Mostrar resumo do mês"""
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        
        if hoje.month == 12:
            ultimo_dia = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)
        
        query = """SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Realizada' THEN 1 ELSE 0 END) as realizadas,
                SUM(CASE WHEN status = 'Agendada' THEN 1 ELSE 0 END) as agendadas,
                SUM(CASE WHEN status = 'Cancelada' THEN 1 ELSE 0 END) as canceladas,
                SUM(CASE WHEN status = 'Realizada' THEN valor ELSE 0 END) as faturamento
                FROM consultas
                WHERE DATE(data_consulta) BETWEEN %s AND %s"""
        
        dados = self.db.execute_query(query, (primeiro_dia, ultimo_dia))
        
        if dados and dados[0][0] > 0:
            total, realizadas, agendadas, canceladas, faturamento = dados[0]
            faturamento = float(faturamento) if faturamento else 0
            
            resumo = f"""RESUMO DO MÊS ({primeiro_dia.strftime('%B/%Y').upper()})

    📊 ESTATÍSTICAS:
    • Total de Consultas: {total}
    • Realizadas: {realizadas}
    • Agendadas: {agendadas}
    • Canceladas: {canceladas}

    💰 FINANCEIRO:
    • Faturamento: R$ {faturamento:.2f}
    • Média por consulta: R$ {(faturamento/realizadas if realizadas > 0 else 0):.2f}

    📈 PERFORMANCE:
    • Taxa de realização: {(realizadas/total*100 if total > 0 else 0):.1f}%
    • Taxa de cancelamento: {(canceladas/total*100 if total > 0 else 0):.1f}%
            """
        else:
            resumo = f"Nenhuma consulta registrada para {primeiro_dia.strftime('%B/%Y')}."
        
        QMessageBox.information(self, "Agenda do Mês", resumo)

    def verificar_consultas_hoje(self):
        """Verificar consultas do dia e mostrar notificações"""
        hoje = date.today()
        
        query = """SELECT c.id, p.nome, c.data_consulta, c.status
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE DATE(c.data_consulta) = %s AND c.status = 'Agendada'
                ORDER BY TIME(c.data_consulta)"""
        
        consultas_hoje = self.db.execute_query(query, (hoje,))
        
        if consultas_hoje:
            nomes = [c[1] for c in consultas_hoje]
            mensagem = f"📅 Você tem {len(consultas_hoje)} consulta(s) agendada(s) para hoje:\n\n"
            
            for consulta in consultas_hoje:
                hora = consulta[2].strftime("%H:%M") if consulta[2] else "Horário não definido"
                mensagem += f"• {hora} - {consulta[1]}\n"
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Consultas de Hoje")
            msg_box.setText(mensagem)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Ignore)
            msg_box.setDefaultButton(QMessageBox.Ok)
            
            btn_agenda = msg_box.addButton("Ver Agenda", QMessageBox.ActionRole)
            
            result = msg_box.exec_()
            
            if msg_box.clickedButton() == btn_agenda:
                self.tab_widget.setCurrentIndex(2)  

    def verificar_consultas_atrasadas(self):
        """Verificar consultas em atraso"""
        agora = datetime.now()
        
        query = """SELECT c.id, p.nome, c.data_consulta
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.data_consulta < %s AND c.status = 'Agendada'
                ORDER BY c.data_consulta DESC"""
        
        consultas_atrasadas = self.db.execute_query(query, (agora,))
        
        if consultas_atrasadas:
            mensagem = f"⚠️ Você tem {len(consultas_atrasadas)} consulta(s) em atraso:\n\n"
            
            for consulta in consultas_atrasadas[:5]:
                data_hora = consulta[2].strftime("%d/%m/%Y %H:%M") if consulta[2] else "Data não definida"
                mensagem += f"• {consulta[1]} - {data_hora}\n"
            
            if len(consultas_atrasadas) > 5:
                mensagem += f"\n... e mais {len(consultas_atrasadas) - 5} consulta(s)"
            
            mensagem += "\n\nDeseja atualizar o status dessas consultas?"
            
            reply = QMessageBox.question(
                self, "Consultas em Atraso", mensagem,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Ignore
            )
            
            if reply == QMessageBox.Yes:
                self.atualizar_consultas_atrasadas()

    def atualizar_consultas_atrasadas(self):
        """Dialog para atualizar status de consultas atrasadas"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Atualizar Consultas Atrasadas")
        dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        agora = datetime.now()
        query = """SELECT c.id, p.nome, c.data_consulta
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.data_consulta < %s AND c.status = 'Agendada'
                ORDER BY c.data_consulta DESC"""
        
        consultas = self.db.execute_query(query, (agora,))
        
        layout.addWidget(QLabel("Selecione as consultas para atualizar:"))
        
        self.lista_atrasadas = QListWidget()
        self.lista_atrasadas.setSelectionMode(QAbstractItemView.MultiSelection)
        
        for consulta in consultas:
            data_hora = consulta[2].strftime("%d/%m/%Y %H:%M")
            texto = f"{consulta[1]} - {data_hora}"
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, consulta[0])
            self.lista_atrasadas.addItem(item)
        
        layout.addWidget(self.lista_atrasadas)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Novo status:"))
        
        self.combo_novo_status = QComboBox()
        self.combo_novo_status.addItems(['Realizada', 'Cancelada'])
        status_layout.addWidget(self.combo_novo_status)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        btn_layout = QHBoxLayout()
        btn_atualizar = QPushButton("Atualizar Selecionadas")
        btn_cancelar = QPushButton("Cancelar")
        
        def atualizar_selecionadas():
            items_selecionados = self.lista_atrasadas.selectedItems()
            if not items_selecionados:
                QMessageBox.warning(dialog, "Aviso", "Selecione pelo menos uma consulta!")
                return
            
            novo_status = self.combo_novo_status.currentText()
            consultas_ids = [item.data(Qt.UserRole) for item in items_selecionados]
            
            for consulta_id in consultas_ids:
                query = "UPDATE consultas SET status = %s WHERE id = %s"
                self.db.execute_insert(query, (novo_status, consulta_id))
            
            QMessageBox.information(dialog, "Sucesso", f"{len(consultas_ids)} consulta(s) atualizada(s)!")
            dialog.accept()
            self.atualizar_consultas()
            self.atualizar_financeiro()
        
        btn_atualizar.clicked.connect(atualizar_selecionadas)
        btn_cancelar.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(btn_atualizar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def inicializar_sistema(self):
        """Inicializar verificações do sistema"""
        QTimer.singleShot(2000, self.verificar_consultas_hoje)
        QTimer.singleShot(3000, self.verificar_consultas_atrasadas) 
        
        self.timer_verificacao = QTimer()
        self.timer_verificacao.timeout.connect(self.verificar_consultas_atrasadas)
        self.timer_verificacao.start(30 * 60 * 1000) 

    def configurar_backup_automatico(self):
        """Configurar backup automático"""
        self.timer_backup = QTimer()
        self.timer_backup.timeout.connect(self.backup_automatico)
        self.timer_backup.start(24 * 60 * 60 * 1000)

    def backup_automatico(self):
        """Realizar backup automático"""
        try:
            from datetime import datetime
            import os
            
            backup_dir = "backups_automaticos"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = os.path.join(backup_dir, f"backup_auto_{timestamp}.txt")
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.write("BACKUP AUTOMÁTICO DO SISTEMA NUTRICIONISTA\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                
                f.write("PACIENTES:\n")
                f.write("-"*30 + "\n")
                pacientes = self.db.execute_query("SELECT * FROM pacientes ORDER BY nome")
                for p in pacientes:
                    f.write(f"ID: {p[0]} | Nome: {p[1]} | Idade: {p[2]} | Sexo: {p[3]} | Peso: {p[4]} | Altura: {p[5]}\n")
                
                f.write("\nCONSULTAS:\n")
                f.write("-"*30 + "\n")
                consultas = self.db.execute_query("""
                    SELECT c.id, p.nome, c.data_consulta, c.status, c.valor 
                    FROM consultas c 
                    JOIN pacientes p ON c.paciente_id = p.id 
                    ORDER BY c.data_consulta DESC
                """)
                for c in consultas:
                    f.write(f"ID: {c[0]} | Paciente: {c[1]} | Data: {c[2]} | Status: {c[3]} | Valor: {c[4]}\n")
                
                f.write("\nPLANOS ALIMENTARES:\n")
                f.write("-"*30 + "\n")
                planos = self.db.execute_query("""
                    SELECT pa.id, p.nome, pa.titulo, pa.objetivo 
                    FROM planos_alimentares pa 
                    JOIN pacientes p ON pa.paciente_id = p.id 
                    ORDER BY pa.data_criacao DESC
                """)
                for pl in planos:
                    f.write(f"ID: {pl[0]} | Paciente: {pl[1]} | Título: {pl[2]} | Objetivo: {pl[3]}\n")
            
            self.limpar_backups_antigos(backup_dir)
            
            self.statusBar().showMessage(f"✅ Backup automático realizado: {backup_filename}", 5000)
            
        except Exception as e:
            print(f"Erro no backup automático: {e}")

    def limpar_backups_antigos(self, backup_dir):
        """Limpar backups com mais de 7 dias"""
        try:
            import os
            from datetime import datetime, timedelta
            
            agora = datetime.now()
            limite = agora - timedelta(days=7)
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("backup_auto_"):
                    filepath = os.path.join(backup_dir, filename)
                    
                    try:
                        date_str = filename.replace("backup_auto_", "").replace(".txt", "")
                        file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        
                        if file_date < limite:
                            os.remove(filepath)
                            
                    except (ValueError, OSError):
                        continue 
                        
        except Exception as e:
            print(f"Erro ao limpar backups antigos: {e}")

class CalculadoraCaloriasDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Calculadora de Calorias")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        self.paciente = QComboBox()
        self.load_pacientes()
        
        self.nivel_atividade = QComboBox()
        self.nivel_atividade.addItems([
            'Sedentário (pouco ou nenhum exercício)',
            'Levemente ativo (exercício leve 1-3 dias por semana)',
            'Moderadamente ativo (exercício moderado 3-5 dias por semana)',
            'Altamente ativo (exercício intenso 6-7 dias por semana)',
            'Extremamente ativo (exercício muito intenso ou trabalho físico)'
        ])
        
        form_layout = QFormLayout()
        form_layout.addRow("Paciente:", self.paciente)
        form_layout.addRow("Nível de Atividade:", self.nivel_atividade)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        self.calcular_btn = QPushButton("Calcular")
        self.cancel_btn = QPushButton("Cancelar")
        
        self.calcular_btn.clicked.connect(self.calculate_calories)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.calcular_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_pacientes(self):
        pacientes = self.db.execute_query("SELECT id, nome FROM pacientes ORDER BY nome")
        self.paciente.clear()
        for p in pacientes:
            self.paciente.addItem(f"{p[1]}", p[0])
    
    def calculate_calories(self):
        paciente_id = self.paciente.currentData()
        if not paciente_id:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente!")
            return
        
        paciente_data = self.db.execute_query(
            "SELECT idade, sexo, peso, altura FROM pacientes WHERE id = %s", (paciente_id,)
        )[0]
        
        if not paciente_data:
            QMessageBox.warning(self, "Erro", "Dados do paciente não encontrados!")
            return
        
        idade, sexo, peso, altura = paciente_data
        nivel_atividade = self.nivel_atividade.currentText()
        
        # Mifflin-St Jeor
        if sexo == 'M':
            bmr = 88.362 + (13.397 * peso) + (4.799 * altura * 100) - (5.677 * idade)
        else:
            bmr = 447.593 + (9.247 * peso) + (3.098 * altura * 100) - (4.330 * idade)
        
        activity_levels = {
            'Sedentário (pouco ou nenhum exercício)': 1.2,
            'Levemente ativo (exercício leve 1-3 dias por semana)': 1.375,
            'Moderadamente ativo (exercício moderado 3-5 dias por semana)': 1.55,
            'Altamente ativo (exercício intenso 6-7 dias por semana)': 1.725,
            'Extremamente ativo (exercício muito intenso ou trabalho físico)': 1.9
        }
        
        tdee = bmr * activity_levels[nivel_atividade]
        
        QMessageBox.information(self, "Resultado", f"O total de calorias diárias necessárias é: {tdee:.2f} kcal")
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())