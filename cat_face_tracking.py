import cv2
import pygame
import threading
import math
import os

#Just to debug once
print("Current working dir:", os.getcwd())
print("Files in this folder:", os.listdir())

#Screen & eye settings 
SCREEN_W, SCREEN_H = 640, 480
EYE_RADIUS = 40         
PUPIL_RADIUS = 14        
SMOOTHING = 0.18         

#Haar cascade path (face detector)
FACE_CASCADE_PATH = r"C:\Users\samri\OneDrive\Documents\coding\cat in screen\haarcascade_frontalface_default.xml"

if not os.path.exists(FACE_CASCADE_PATH):
    print("ERROR: haarcascade_frontalface_default.xml not found at:")
    print(FACE_CASCADE_PATH)
    raise SystemExit

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
if face_cascade.empty():
    print("ERROR: face_cascade is empty. XML file might be corrupted.")
    raise SystemExit

# webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open webcam")
    raise SystemExit

# normalized face coords (0..1)
face_norm_x = 0.5
face_norm_y = 0.5

def webcam_loop():
    """
    Runs in a separate thread.
    Continuously reads frames from webcam and updates face_norm_x, face_norm_y.
    """
    global face_norm_x, face_norm_y
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces in the frame
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5
        )

        h, w = gray.shape[:2]

        if len(faces) > 0:
            # take the biggest face (closest)
            x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            cx = x + fw / 2
            cy = y + fh / 2

            # convert to normalized coordinates (0..1)
            face_norm_x = cx / w
            face_norm_y = cy / h


# Init pygame 
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
pygame.display.set_caption("Doe-Eye Cat - Face Tracking 🐱")

left_eye_center = (int(SCREEN_W * 0.33), int(SCREEN_H * 0.45))
right_eye_center = (int(SCREEN_W * 0.66), int(SCREEN_H * 0.45))

pupil_norm = [0.5, 0.5]
pupil_smooth = [0.5, 0.5]

# Start the webcam thread 
t = threading.Thread(target=webcam_loop, daemon=True)
t.start()

def pupil_screen(center, normpos):
    """
    Convert normalized pupil position (0..1) to screen coordinates inside one eye.

    center: (x, y) of eye center
    normpos: [nx, ny] where 0.5 is center, 0..1 is movement range
    """
    max_offset = EYE_RADIUS - PUPIL_RADIUS - 4
    offset_x = (normpos[0] - 0.5) * max_offset * 1.8   # horizontal movement
    offset_y = (normpos[1] - 0.5) * max_offset * 1.2   # vertical movement

    return int(center[0] + offset_x), int(center[1] + offset_y)


# Main loop 
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    target_x = face_norm_x  
    target_y = face_norm_y  

    # Limit range a bit so pupils stay inside cute zone
    target_x = max(0.15, min(0.85, target_x))
    target_y = max(0.20, min(0.80, target_y))

    pupil_norm[0] = target_x
    pupil_norm[1] = target_y

    # Smooth movement to avoid jitter
    pupil_smooth[0] += (pupil_norm[0] - pupil_smooth[0]) * SMOOTHING
    pupil_smooth[1] += (pupil_norm[1] - pupil_smooth[1]) * SMOOTHING

    screen.fill((250, 240, 245))  

    # head circle
    pygame.draw.circle(screen, (255, 230, 240), (SCREEN_W // 2, SCREEN_H // 2), 170)

    # eyes white
    pygame.draw.circle(screen, (255, 255, 255), left_eye_center, EYE_RADIUS)
    pygame.draw.circle(screen, (255, 255, 255), right_eye_center, EYE_RADIUS)

    # pupils follow face
    pl = pupil_screen(left_eye_center, pupil_smooth)
    pr = pupil_screen(right_eye_center, pupil_smooth)
    pygame.draw.circle(screen, (30, 30, 30), pl, PUPIL_RADIUS)
    pygame.draw.circle(screen, (30, 30, 30), pr, PUPIL_RADIUS)

    # small highlight in pupils
    highlight_offset = (-4, -4)
    pygame.draw.circle(screen, (255, 255, 255),
                       (pl[0] + highlight_offset[0], pl[1] + highlight_offset[1]), 4)
    pygame.draw.circle(screen, (255, 255, 255),
                       (pr[0] + highlight_offset[0], pr[1] + highlight_offset[1]), 4)

    # blush cheeks
    pygame.draw.circle(screen, (255, 180, 200),
                       (SCREEN_W // 2 - 55, SCREEN_H // 2 + 30), 18)
    pygame.draw.circle(screen, (255, 180, 200),
                       (SCREEN_W // 2 + 55, SCREEN_H // 2 + 30), 18)

    # mouth arc
    pygame.draw.arc(
        screen,
        (120, 50, 70),
        (SCREEN_W // 2 - 40, SCREEN_H // 2 + 10, 80, 60),
        math.radians(20),
        math.radians(160),
        3,
    )

    # text
    font = pygame.font.SysFont(None, 20)
    txt = font.render("Move your head: cat eyes follow your face 💖", True, (80, 80, 90))
    screen.blit(txt, (10, SCREEN_H - 30))

    pygame.display.flip()
    clock.tick(30)

#Cleanup 
cap.release()
pygame.quit()
