import pygame
import mido
import sys
import colorsys

# Función para leer las notas desde el archivo de texto
def read_notes_from_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            notes = [int(note.strip()) for note in content.split(',')]
            return notes
    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
    except ValueError:
        print(f"Invalid format in {filename}.")
        sys.exit(1)

# Leer las notas desde el archivo
notes_file = 'notas.txt'
NOTES_LIST = read_notes_from_file(notes_file)
NOTES = len(NOTES_LIST)

# Configuración inicial de pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Kaossilator-like Synth")

# Listar dispositivos MIDI disponibles
midi_output_names = mido.get_output_names()
if not midi_output_names:
    print("No MIDI output devices found.")
    sys.exit(1)

print("Available MIDI output devices:")
for i, name in enumerate(midi_output_names):
    print(f"{i}: {name}")

# Seleccionar el dispositivo MIDI virtual creado por loopMIDI
virtual_midi_port_name = 'loopMIDI Port 1'
if virtual_midi_port_name not in midi_output_names:
    print(f"{virtual_midi_port_name} not found in available MIDI output devices.")
    sys.exit(1)

midi_output = mido.open_output(virtual_midi_port_name)

def get_midi_note_from_x(x, width):
    note_index = int(x / width * NOTES)
    return NOTES_LIST[note_index]

def get_control_value_from_y(y, height):
    return int(127 - 127 * y / height)

def get_color_for_note(note, min_note, max_note):
    # Convertir la posición de la nota en el rango de 0 a 1
    position = (note - min_note) / (max_note - min_note)
    # Calcular el color desde 0.75 (violeta) hasta 0 (rojo)
    hue = 0.75 - 0.75 * position
    rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

# Estado de la aplicación
current_note = None
current_control_value = 0  # Definición inicial

left_click_pressed = False

# Loop principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Click izquierdo
                left_click_pressed = True
                # Obtener la posición del cursor
                x, y = event.pos
                width, height = screen.get_size()
                # Obtener la nota MIDI y el valor de control
                midi_note = get_midi_note_from_x(x, width)
                control_value = get_control_value_from_y(y, height)
                # Enviar mensaje de nota ON
                note_on = mido.Message('note_on', note=midi_note, velocity=64)
                midi_output.send(note_on)
                # Enviar mensaje de cambio de control
                control_change = mido.Message('control_change', control=1, value=control_value)
                midi_output.send(control_change)
                # Imprimir mensajes de depuración
                print(f"Sent MIDI Note: {midi_note}")
                print(f"Sent Control Value: {control_value}")
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Soltar click izquierdo
                left_click_pressed = False
                if current_note is not None:
                    note_off = mido.Message('note_off', note=current_note, velocity=64)
                    midi_output.send(note_off)
                    current_note = None
        elif event.type == pygame.MOUSEMOTION:
            if left_click_pressed:
                x, y = event.pos
                width, height = screen.get_size()
                midi_note = get_midi_note_from_x(x, width)
                control_value = get_control_value_from_y(y, height)

                if current_note != midi_note:
                    if current_note is not None:
                        note_off = mido.Message('note_off', note=current_note, velocity=64)
                        midi_output.send(note_off)
                    current_note = midi_note
                    note_on = mido.Message('note_on', note=midi_note, velocity=64)
                    midi_output.send(note_on)
                    print(f"Sent MIDI Note: {midi_note}")

                if current_control_value != control_value:
                    current_control_value = control_value
                    control_change = mido.Message('control_change', control=1, value=control_value)
                    midi_output.send(control_change)
                    print(f"Sent Control Value: {control_value}")

    # Dibujar la pantalla y el círculo del cursor
    screen.fill((0, 0, 0))
    if left_click_pressed:
        color = get_color_for_note(midi_note, min(NOTES_LIST), max(NOTES_LIST))
        pygame.draw.circle(screen, color, pygame.mouse.get_pos(), 15)
    pygame.display.flip()

pygame.quit()