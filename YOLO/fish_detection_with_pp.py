#Dependencies:
#1. OpenCV
from asyncio.windows_events import NULL
import gc
import cv2
import time
import numpy as np
from imutils.video import WebcamVideoStream

gc.collect()

#Load YOLOv3 algorithm
net = cv2.dnn.readNet("yolov3-fish.weights", "yolov3-obj.cfg")
classes = []
with open("coco_names.txt", "r") as f:
    classes = [line.strip() for line in f.readlines()]

#get the output layers for the YOLOv3 algorithm
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

vs = WebcamVideoStream(src="fish_vid.mp4").start()
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
font = cv2.FONT_HERSHEY_PLAIN
starting_time= time.time()
frame_id = 0
desired_obj = input("Enter the desired obj: ")
while True:
    frame= vs.read()
    frame_id+=1
    #perform CLAHE
    b = clahe.apply(frame[:, :, 0])
    g = clahe.apply(frame[:, :, 1])
    r = clahe.apply(frame[:, :, 2])
    pp_frame = np.dstack((b, g, r))

    #remove noise
    #pp_frame = cv2.fastNlMeansDenoisingColored(pp_frame, None, 10, 10, 7, 15)
    pp_frame = cv2.bilateralFilter(pp_frame, 5, 65, 65)
    height,width,channels = frame.shape
    #detecting objects
    blob = cv2.dnn.blobFromImage(pp_frame,0.00392,(320,320),(0,0,0),True,crop=False) #reduce 416 to 320    

    net.setInput(blob)
    outs = net.forward(output_layers)

    #Showing info on screen/ get confidence score of algorithm in detecting an object in blob
    class_ids=[]
    confidences=[]
    boxes=[]
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence >= 0.5 and classes[class_id]==desired_obj:

                center_x= int(detection[0]*width)
                center_y= int(detection[1]*height)
                w = int(detection[2]*width)
                h = int(detection[3]*height)
                x=int(center_x - w/2)
                y=int(center_y - h/2)

                boxes.append([x,y,w,h]) 
                confidences.append(float(confidence)) 

    indexes = cv2.dnn.NMSBoxes(boxes,confidences,0.5,0.4)


    for i in range(len(boxes)):
        if i in indexes:
            x,y,w,h = boxes[i]
            confidence= confidences[i]
            cv2.rectangle(pp_frame,(x,y),(x+w,y+h),(0,0,0),2)
            cv2.putText(pp_frame,str(round(confidence,2)),(x,y+30),font,1,(255,255,255),2)
            

    elapsed_time = time.time() - starting_time
    fps=frame_id/elapsed_time
    cv2.putText(pp_frame,"FPS:"+str(round(fps,2)),(10,50),font,2,(0,0,0),1)
    cv2.imshow("Video",pp_frame)
    key = cv2.waitKey(1) 
    if key == 27: #esc key stops the process
        break
    
vs.stop()    
cv2.destroyAllWindows()    
