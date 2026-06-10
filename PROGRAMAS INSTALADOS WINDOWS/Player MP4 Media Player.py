import sys
import os

# pip install PyQt6 PyQt6-WebEngine 

# ====================== SUPRIMIR LOGS DO QT MULTIMEDIA ======================
os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false;qt.ffmpeg*=false;*.debug=false;*.info=false;*.warning=false"
os.environ["QT_QPA_PLATFORM"] = "windows"  # Mais estável no Windows

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QFileDialog, QSlider, QVBoxLayout,
    QHBoxLayout, QLabel
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut


class Player(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Player MP4 Media Player")
        self.resize(1200, 720)
        self.showMaximized()
        self.setWindowIcon(QIcon.fromTheme("video-x-generic"))

        # Player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)

        self.video = QVideoWidget()
        self.player.setVideoOutput(self.video)

        # Controles
        self.btn_abrir = QPushButton("Abrir")
        self.btn_play = QPushButton("▶ Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_fullscreen = QPushButton("⛶ Fullscreen")

        # Barra de progresso
        self.barra = QSlider(Qt.Orientation.Horizontal)
        self.barra.setRange(0, 0)

        # Volume
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)

        # Label de tempo
        self.label_tempo = QLabel("00:00 / 00:00")
        self.label_tempo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Conexões
        self.btn_abrir.clicked.connect(self.abrir_video)
        self.btn_play.clicked.connect(self.player.play)
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_stop.clicked.connect(self.player.stop)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)

        self.player.positionChanged.connect(self.atualizar_posicao)
        self.player.durationChanged.connect(self.atualizar_duracao)

        self.barra.sliderMoved.connect(self.mover_video)

        self.volume.valueChanged.connect(
            lambda v: self.audio.setVolume(v / 100.0)
        )

        # Atalhos de teclado
        self.shortcut_full = QShortcut(QKeySequence("F11"), self)
        self.shortcut_full.activated.connect(self.toggle_fullscreen)

        self.shortcut_esc = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_esc.activated.connect(self.exit_fullscreen)

        # Duplo clique no vídeo
        self.video.mouseDoubleClickEvent = self.mouse_double_click

        # Layout
        botoes = QHBoxLayout()
        botoes.addWidget(self.btn_abrir)
        botoes.addWidget(self.btn_play)
        botoes.addWidget(self.btn_pause)
        botoes.addWidget(self.btn_stop)
        botoes.addWidget(self.btn_fullscreen)

        layout = QVBoxLayout()
        layout.addWidget(self.video, stretch=1)
        layout.addWidget(self.barra)
        layout.addWidget(self.label_tempo)
        layout.addLayout(botoes)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume)
        layout.addLayout(volume_layout)

        self.setLayout(layout)

    def formatar_tempo(self, ms):
        if ms < 0:
            return "00:00"
        segundos = int(ms / 1000)
        minutos = segundos // 60
        horas = minutos // 60
        minutos %= 60
        segundos %= 60

        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return f"{minutos:02d}:{segundos:02d}"

    def abrir_video(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Abrir Vídeo", "", "Vídeos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)"
        )
        if arquivo:
            self.player.setSource(QUrl.fromLocalFile(arquivo))
            self.player.play()

    def atualizar_posicao(self, pos):
        self.barra.setValue(pos)
        duracao = self.player.duration()
        self.label_tempo.setText(
            f"{self.formatar_tempo(pos)} / {self.formatar_tempo(duracao)}"
        )

    def atualizar_duracao(self, dur):
        self.barra.setRange(0, dur)
        pos = self.player.position()
        self.label_tempo.setText(
            f"{self.formatar_tempo(pos)} / {self.formatar_tempo(dur)}"
        )

    def mover_video(self, pos):
        self.player.setPosition(pos)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.showFullScreen()

    def exit_fullscreen(self):
        self.showNormal()

    def mouse_double_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_fullscreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    janela = Player()
    janela.show()
    
    sys.exit(app.exec())
