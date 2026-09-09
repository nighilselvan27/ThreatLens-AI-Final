from app.services.ember_extractor import extract_ember_features

# Replace this with the path to a safe PE (.exe) file
file_path = r"C:\Users\GAYATHRI\Downloads\normal.exe"

features = extract_ember_features(file_path)

print("Shape:", features.shape)
print(features.head())