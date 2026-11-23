'''Attention! Ce code fonctionne avec mon setup, pour le reproduire il fuat une vue du dessus, sur un fond noir/gris, et avec une position des doigts très précise'''

import cv2
import numpy as np
from image_processing import trouver_contour
import etat

#pour palier le problème du contours discontinus, on relie les contours aux bords de l'image
def relier_aux_bords(image):
    resultat = image.copy()
    hauteur, largeur = image.shape
    bords = (
        (image[:2, :], 0, lambda p: (p, 0), lambda p: (p, 1)),
        (image[-2:, :], 0, lambda p: (p, hauteur - 1), lambda p: (p, hauteur - 2)),
        (image[:, :2], 1, lambda p: (0, p), lambda p: (1, p)),
        (image[:, -2:], 1, lambda p: (largeur - 1, p), lambda p: (largeur - 2, p)),
    )

    for zone, axe, sur_bord, pres_bord in bords:
        positions = np.flatnonzero(np.any(zone, axis=axe))
        if len(positions) == 0:
            continue
        groupes = np.split(positions, np.where(np.diff(positions) > 1)[0] + 1)
        if len(groupes) != 2:
            continue

        debut = int(groupes[0][len(groupes[0]) // 2])
        fin = int(groupes[1][len(groupes[1]) // 2])
        cv2.line(resultat, pres_bord(debut), sur_bord(debut), 255, 1)
        cv2.line(resultat, sur_bord(debut), sur_bord(fin), 255, 1)
        cv2.line(resultat, sur_bord(fin), pres_bord(fin), 255, 1)

    return resultat

#boucle principale pour le comptage des doigts

def prise_de_decision():
    
    prises = []
    nombre_prises = 15
    nombre_images = 0
    
    while not etat.fin:
        
        image_contour, contours = trouver_contour()
        nombre_images += 1
        masque = np.zeros(image_contour.shape[:2], dtype=np.uint8)
        
        if len(contours) > 0:
        # On prend le plus grand contour pour le traitement ultérieur
            largest = max(contours, key=cv2.contourArea)
            bordure = np.zeros_like(masque)
            cv2.drawContours(bordure, [largest], -1, 255, 1)
            bordure = relier_aux_bords(bordure)
            contours_relies, _ = cv2.findContours(bordure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours_relies:
                largest = max(contours_relies, key=cv2.contourArea)
                cv2.drawContours(masque, [largest], -1, 255, cv2.FILLED)
            contours_nettoyes, _ = cv2.findContours(masque, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # On prend le plus grand contour nettoyé pour le traitement ultérieur
            if contours_nettoyes:
                contour_nettoye = max(contours_nettoyes, key=cv2.contourArea)
                enveloppe = cv2.convexHull(contour_nettoye, returnPoints=False)

                if len(enveloppe) >= 3:
                        defauts = cv2.convexityDefects(contour_nettoye, enveloppe)
                        nombre_creux = len(defauts)
                        prises.append(nombre_creux)
                        print(f"Nombre de creux : {nombre_creux}")
        
        cv2.imshow("Plus grand contour trouvé", image_contour)
        cv2.imshow("Masque rempli", masque)
        
        if cv2.waitKey(1) == 27 or nombre_images >= nombre_prises:
            etat.fin = True

    if len(prises) == nombre_prises:
        
        moyenne = sum(prises) / len(prises)
        print(f"Moyenne : {moyenne:.2f}")
        
        if 10 <= moyenne <= 35:
            references = {"papier":15, "ciseaux": 20, "pierre": 29.0}
            resultat = min(references, key=lambda geste: abs(moyenne - references[geste]))
            print("Geste estime :", resultat)
            return resultat
        
    else:
        print("echec de la mesure")
        return None
    
        
    cv2.destroyAllWindows()    
    
    
prise_de_decision()
