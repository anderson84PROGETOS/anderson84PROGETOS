import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import time
import csv
from datetime import datetime
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import os

# === CONFIGURAÇÕES ===
USE_REAL_DEVICE = True            # Mude para True se estiver usando dispositivo real    False, o código não tentará se conectar a um dispositivo
SERIAL_PORT = 'COM1'                # Ex: COM3 no Windows ou /dev/ttyUSB0 no Linux
BAUD_RATE = 115200
NUM_SAMPLES = 200
MAX_SUBCARRIERS = 128
MOVEMENT_THRESHOLD = 5.0
MIN_MOVEMENT_INTERVAL = 3.0
BUFFER_SIZE = 50
VARIATION_SMOOTHING_WINDOW = 5     # Deve ser ímpar  5, 7, 9, 11, 13, o sistema ficará mais sensível a movimentos
DEBUG_MODE = True

# === VARIÁVEIS ===
csi_matrix = np.zeros((NUM_SAMPLES, MAX_SUBCARRIERS))
selected_subcarriers = list(range(0, MAX_SUBCARRIERS, 10))
vertical_offsets = np.arange(MAX_SUBCARRIERS) * 50
movement_detected = False
animation_counter = 0
variation_buffer = []
last_movement_time = time.time()
ser = None

# === INICIALIZAR SERIAL ===
def init_serial():
    global ser
    if USE_REAL_DEVICE:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"[✓] Porta serial {SERIAL_PORT} aberta com sucesso.")
        except serial.SerialException as e:
            print(f"[X] Falha ao abrir a porta serial: {e}")
            exit()

# === GERAÇÃO DE DADOS FALSOS ===
def generate_fake_csi():
    base = np.random.normal(loc=50, scale=5, size=MAX_SUBCARRIERS)
    if np.random.rand() < 0.1:
        base += np.random.normal(0, 20, size=MAX_SUBCARRIERS)
    return base

# === PROCESSAMENTO DOS DADOS ===
def process_csi_data(data_line):
    try:
        decoded = data_line.decode().strip()
        if not decoded:
            return None
        parts = decoded.split(',')
        if len(parts) != MAX_SUBCARRIERS:
            if DEBUG_MODE:
                print(f"[!] Dados com tamanho inválido ({len(parts)}): {decoded}")
            return None
        return np.array([float(x) for x in parts])
    except Exception as e:
        if DEBUG_MODE:
            print(f"[!] Erro ao processar dados: {e}")
        return None

# === CÁLCULO DE VARIAÇÃO ===
def calculate_variation(csi_data):
    if len(variation_buffer) >= BUFFER_SIZE:
        variation_buffer.pop(0)
    variation_buffer.append(csi_data)

    if len(variation_buffer) < 2:
        return 0

    diff = np.abs(np.diff(np.array(variation_buffer), axis=0))
    variation = np.mean(diff)

    if len(variation_buffer) >= VARIATION_SMOOTHING_WINDOW:
        variation = savgol_filter(
            [np.mean(np.abs(np.diff(
                np.array(variation_buffer[-VARIATION_SMOOTHING_WINDOW:]), axis=0)))
             for _ in range(VARIATION_SMOOTHING_WINDOW)],
            VARIATION_SMOOTHING_WINDOW, 3)[-1]

    return variation

# === DESENHO DO BONECO ===
def draw_stickman(ax, move=False):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 15)
    ax.axis('off')

    head = patches.Circle((5, 13), 1, fill=False, linewidth=2)
    ax.add_patch(head)
    ax.plot([5, 5], [12, 8], color='black', linewidth=2)

    if move:
        ax.plot([5, 4], [11, 10], color='black', linewidth=2)
        ax.plot([5, 6], [11, 10], color='black', linewidth=2)
        ax.plot([5, 4.5], [8, 6], color='black', linewidth=2)
        ax.plot([5, 5.5], [8, 6], color='black', linewidth=2)
    else:
        ax.plot([5, 3.5], [11, 10.5], color='black', linewidth=2)
        ax.plot([5, 6.5], [11, 10.5], color='black', linewidth=2)
        ax.plot([5, 4.8], [8, 6.5], color='black', linewidth=2)
        ax.plot([5, 5.2], [8, 6.5], color='black', linewidth=2)

# === ATUALIZAÇÃO DO FRAME ===
def update(frame):
    global csi_matrix, movement_detected, animation_counter, last_movement_time

    try:
        if USE_REAL_DEVICE:
            line = ser.readline()
        else:
            line = b",".join(map(str.encode, map(str, generate_fake_csi()))) + b"\n"

        csi_data = process_csi_data(line)
        if csi_data is None:
            return []

        csi_matrix[:-1] = csi_matrix[1:]
        csi_matrix[-1] = csi_data

        variation = calculate_variation(csi_data)
        current_time = time.time()

        movement_detected = (
            variation > MOVEMENT_THRESHOLD and
            current_time - last_movement_time > MIN_MOVEMENT_INTERVAL
        )

        if movement_detected:
            last_movement_time = current_time

        ax1.clear()
        ax2.clear()
        ax3.clear()

        ax1.imshow(csi_matrix.T, aspect='auto', interpolation='nearest', cmap='viridis')
        ax1.set_title('CSI Matrix')
        ax1.set_xlabel('Tempo')
        ax1.set_ylabel('Subportadora')

        for i in selected_subcarriers:
            ax2.plot(csi_matrix[:, i] + vertical_offsets[i], label=f'Sub {i}')
        ax2.set_title('Amplitude Subportadoras')
        ax2.set_xlabel('Tempo')
        ax2.set_ylabel('Amplitude')

        draw_stickman(ax3, move=movement_detected)

        if movement_detected:
            ax2.text(0.02, 0.98, 'MOVIMENTO DETECTADO', transform=ax2.transAxes,
                     color='red', fontsize=12, verticalalignment='top')

        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] +
                            list(csi_data) + [variation, movement_detected])

        status = "SIM" if movement_detected else "NÃO"
        print(f"[{animation_counter}] Variação: {variation:.2f} | Movimento detectado: {status}")

        animation_counter += 1

    except Exception as e:
        print(f"[!] Erro no frame: {e}")
    return []

# === INÍCIO DO PROGRAMA ===
init_serial()
csv_filename = f'csi_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp'] + [f'Subcarrier_{i}' for i in range(MAX_SUBCARRIERS)] +
                    ['Variation', 'Movement'])

fig = plt.figure(figsize=(14, 10))
ax1 = fig.add_subplot(3, 1, 1)
ax2 = fig.add_subplot(3, 1, 2)
ax3 = fig.add_subplot(3, 1, 3)

try:
    ani = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()
finally:
    if ser:
        ser.close()
        print("[✓] Porta serial fechada.")
