import cv2
import pytesseract
import os, re
import Levenshtein
pytesseract.pytesseract.tesseract_cmd = r'C:/Users/prabh/Tesseract-OCR/tesseract.exe'

parameters = {'Date of Birth': False, 'Address': False, 'Expiration Date': False, 'Blood Type': False, 'Agency Code': False, 'Eyes Color': False}

def list_files_in_folder(folder_path):
    file_paths = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    
    return file_paths

def is_face_visible(image_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    img = cv2.imread(image_path)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) > 0:
        return True
    else:
        return False

def find_similar_parts(target, input_text, threshold = 0.60):
    similar_parts = []
    words = input_text.split()
    
    for i in range(len(words)):
        for j in range(i+1, len(words) + 1):
            part = ' '.join(words[i:j])
            similarity = 1 - Levenshtein.distance(target, part) / max(len(target), len(part))
            if similarity >= threshold:
                similar_parts.append((part, similarity))
    
    similar_parts.sort(key=lambda x: x[1], reverse=True)
    if similar_parts:
        return similar_parts[0][0]
    else:
        return False

def compare_left_allignment(part,strings,extracts):
    if(strings == "Date of Birth" or strings == "Expiration Date"):
        pattern = '^(19|20)\d\d/(0[1-9]|1[012])/(0[1-9]|[12][0-9]|3[01])$'
        coord_list = []
        n_boxes = len(extracts['text'])
        for i in range(n_boxes):
            if int(extracts['conf'][i]) > 10:
                if re.match(pattern, extracts['text'][i]):
                    (x, y, w, h) = (extracts['left'][i], extracts['top'][i], extracts['width'][i], extracts['height'][i])
                    coord_list.append(x)
                if extracts['text'][i] == part.split(' ')[0]:
                    (x, y, w, h) = (extracts['left'][i], extracts['top'][i], extracts['width'][i], extracts['height'][i])
                    coord_list.append(x)
                if len(coord_list) == 2:
                    if coord_list[0] - coord_list[1] <= 5:
                        return True
                    else:
                        return False

    if(strings == "Address"):
        return True

def compare_center_allignment(part,strings,extracts):
    pattern = " "
    if(strings == "Blood Type"):
        return True
    if(strings == "Agency Code"):
        return True
    if(strings == "Eyes Color"):
        pattern = '^(BLACK|BLUE|GRAY|BROWN|black)$'
    coordinate = 0
    coord_list = []
    n_boxes = len(extracts['text'])
    for i in range(n_boxes):
        if int(extracts['conf'][i]) > 10:
            if re.match(pattern, extracts['text'][i]):
                (x, y, w, h) = (extracts['left'][i], extracts['top'][i], extracts['width'][i], extracts['height'][i])
                coordinate += x + w/2
                coord_list.append(x)
            if extracts['text'][i] in part.split(' '):
                (x, y, w, h) = (extracts['left'][i], extracts['top'][i], extracts['width'][i], extracts['height'][i])
                if extracts['text'][i] == part.split(' ')[0]:
                    coordinate -= (x+w/2)
                    coord_list.append(x)
                else:
                    coordinate -= w/2

    if abs(coordinate) <= 5 and len(coord_list) == 2 and abs(coord_list[0] - coord_list[1]) >= 1:
        return True
    else:
        return False


def isFaceVisible(gray_image):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces)>0

def multyProcessImages(image_path):
    images = []
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    images.append(gray_image)

    gussian_image = cv2.GaussianBlur(src=gray_image,ksize=(3, 3), sigmaX=0,sigmaY=0)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(12, 12))
    clached_image = clahe.apply(gray_image)

    unsharp_image = cv2.addWeighted(clached_image, 2.0, gray_image, -1.0, 0)

    _, thresold_image1 = cv2.threshold(gussian_image, thresh=165, maxval=255, type=cv2.THRESH_TRUNC + cv2.THRESH_OTSU)
    images.append(thresold_image1)

    _, thresold_image2 = cv2.threshold(gray_image, thresh=165, maxval=255, type=cv2.THRESH_TRUNC + cv2.THRESH_OTSU)
    images.append(thresold_image2)

    _, thresold_image3 = cv2.threshold(clached_image, thresh=165, maxval=255, type=cv2.THRESH_TRUNC + cv2.THRESH_OTSU)
    images.append(thresold_image3)

    _, thresold_image4 = cv2.threshold(unsharp_image, thresh=165, maxval=255, type=cv2.THRESH_TRUNC + cv2.THRESH_OTSU)
    images.append(thresold_image4)
    
    return images

def fillStatus(image,left_list,centerd_list):
    global parameters
    extracts = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    extracted_text = pytesseract.image_to_string(image)
    for strings in left_list:
        part = find_similar_parts(strings,extracted_text)     
        if(part != False):
            if(compare_left_allignment(part, strings, extracts)):
                parameters[strings] = True
    
    for strings in centerd_list:
        part = find_similar_parts(strings,extracted_text)     
        if(part != False):
            if(compare_center_allignment(part, strings, extracts)):
                parameters[strings] = True

def computeStatus(procesd_images,left_list,centerd_list):
    status = {'msimatch percentage': 0.0, 'face visibility': False, 'matched parameters': [], 'mismatched parameters': []}
    mmpercentage = 0.0
        
    face_visibility = isFaceVisible(procesd_images[0])
    
    if face_visibility:
        status['face visibility'] = True
    else:
        mmpercentage += 33.33

    for image in procesd_images:
        fillStatus(image,left_list,centerd_list)

    for key in parameters:
        if parameters[key]:
            status['matched parameters'].append(key)
        else:
            status['mismatched parameters'].append(key)
            mmpercentage += 11.11
    
    status['msimatch percentage'] = mmpercentage
            
    return status

def findMissMatchPercentage(image_path):
    processedImages = multyProcessImages(image_path)
    left_aligned_list = ["Date of Birth", "Address", "Expiration Date"]
    center_aligned_list = ["Blood Type", "Agency Code", "Eyes Color"]
    status = computeStatus(processedImages, left_aligned_list, center_aligned_list)
    file_name = os.path.basename(image_path)

    print(file_name)
    for key in status.keys():
        #print the file name 
        print(key, ":", status[key])
    print()
    return status

if __name__ == "__main__":
    directory = input("Please enter the path of the directory that contains the images:")
    files = list_files_in_folder(directory)
    for file in files:
        parameters = {'Date of Birth': False, 'Address': False, 'Expiration Date': False, 'Blood Type': False, 'Agency Code': False, 'Eyes Color': False}
        findMissMatchPercentage(str(file))

