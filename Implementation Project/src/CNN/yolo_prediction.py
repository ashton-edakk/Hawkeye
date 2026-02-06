from ultralytics import YOLO

model = YOLO(r"C:\Users\ashto\Documents\440-Group-4-Spring-2026\Implementation Project\src\CNN\runs\detect\train4\weights\best.pt")

results = model(r"C:\Users\ashto\Documents\440-Group-4-Spring-2026\Implementation Project\src\CNN\datasets\african-wildlife\images\test\1 (179).jpg", save=True)