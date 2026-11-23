import cv2
import numpy as np
import etat

def trouver_contour():
    
    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()
        
        #flou gaussien
        blur = cv2.GaussianBlur(frame, (7, 7), 0) 
        
        # détection des contours avec le gradient L2
        edges2 = cv2.Canny(blur, 100, 150, L2gradient=True) 
        
        images = [frame,edges2]
        titles = ['Original','L2 Gradient']
        
        # noyau pour la fermeture morphologique
        kernel = np.ones((6, 6), dtype=np.uint8) 
        
        # fermeture morphologique pour combler les trous
        fermeture = cv2.morphologyEx(edges2, cv2.MORPH_CLOSE, kernel) 
        
        
        # création masque lisse pour stabiliser les contours dans le temps
        if 'masque_lisse' not in locals():
            masque_lisse = fermeture.astype(np.float32)
        else:
            cv2.accumulateWeighted(fermeture, masque_lisse, 0.2)

        masque_stable = cv2.convertScaleAbs(masque_lisse)
        _, masque_stable = cv2.threshold(masque_stable, 100, 255, cv2.THRESH_BINARY)

        # recherche des contours externes
        contours, _ = cv2.findContours(fermeture, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

        # affichage mask stable pour visualiser les contours apres mask
        image_stable = np.zeros_like(frame)
        
        cv2.drawContours(image_stable, contours, -1, (0, 255, 0), 2)
        
        # sélectionplus grand contour pour affichage
        image_contour = np.zeros_like(frame)
        if len(contours) > 0:
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(image_contour, [largest], -1, (0, 255, 0), 2)
            
        #Affichage commenté car on est dans finger_count.py    
            #cv2.imshow("Plus grand contour trouvé", image_contour)
            #cv2.imshow("Contours stable (masque)", image_stable)
            #cv2.imshow("Original", frame)
        
        if etat.fin == True:
            break
        
        return image_contour, contours
    
    cap.release()
    cv2.destroyAllWindows()