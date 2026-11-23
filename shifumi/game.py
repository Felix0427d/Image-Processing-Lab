import os
import random
import re
import subprocess
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import messagebox


DOSSIER = Path(__file__).resolve().parent
GESTES = ("pierre", "papier", "ciseaux")


def lire_geste(sortie):
    match = re.search(
        r"^\s*Geste\s+estim(?:e|é)\s*:\s*(pierre|papier|ciseaux?)\s*$",
        sortie,
        re.IGNORECASE | re.MULTILINE,
    )
    if match is None:
        raise ValueError("Le script n'a pas renvoyé un geste reconnu.")
    geste = match.group(1).lower()
    return "ciseaux" if geste == "ciseau" else geste


def resultat_manche(joueur, ordinateur):
    if joueur == ordinateur:
        return "Égalité !"
    gagne_contre = {"pierre": "ciseaux", "papier": "pierre", "ciseaux": "papier"}
    return "Vous gagnez !" if gagne_contre[joueur] == ordinateur else "L'ordinateur gagne !"


class Jeu:
    def __init__(self, fenetre):
        self.fenetre = fenetre
        self.fenetre.title("Pierre, papier, ciseaux")
        self.fenetre.geometry("440x350")
        self.fenetre.resizable(False, False)
        self.fenetre.configure(bg="#f1f5f9")
        self.fenetre.protocol("WM_DELETE_WINDOW", self.fermer)

        self.processus = None
        self.futur = None
        self.tache = ThreadPoolExecutor(max_workers=1)

        tk.Label(
            fenetre, text="Pierre  •  Papier  •  Ciseaux",
            font=("Segoe UI", 18, "bold"), bg="#f1f5f9", fg="#172554"
        ).pack(pady=(30, 12))
        self.instruction = tk.Label(
            fenetre, text="Placez votre main devant la caméra.",
            font=("Segoe UI", 11), bg="#f1f5f9", fg="#475569"
        )
        self.instruction.pack()
        self.compteur = tk.Label(
            fenetre, text="Prêt ?", font=("Segoe UI", 26, "bold"),
            bg="#f1f5f9", fg="#2563eb"
        )
        self.compteur.pack(pady=18)
        self.detail = tk.Label(
            fenetre, text="", font=("Segoe UI", 11),
            bg="#f1f5f9", fg="#172554"
        )
        self.detail.pack()
        self.bouton = tk.Button(
            fenetre, text="Jouer", command=self.jouer,
            font=("Segoe UI", 11, "bold"), bg="#2563eb", fg="white",
            activebackground="#1d4ed8", activeforeground="white",
            relief="flat", padx=25, pady=8
        )
        self.bouton.pack(pady=20)

    def jouer(self):
        self.bouton.config(state="disabled")
        self.detail.config(text="")
        self.instruction.config(text="Préparez votre geste.")
        self.decompte(3)

    def decompte(self, nombre):
        if nombre > 0:
            self.compteur.config(text=str(nombre))
            self.fenetre.after(1000, self.decompte, nombre - 1)
        else:
            self.compteur.config(text="Détection...")
            self.instruction.config(text="Gardez votre geste immobile.")
            self.fenetre.after(50, self.lancer_detection)

    def lancer_detection(self):
        environnement = os.environ.copy()
        environnement["PYTHONIOENCODING"] = "utf-8"
        try:
            self.processus = subprocess.Popen(
                [sys.executable, "-u", str(DOSSIER / "finger_sign.py")],
                cwd=DOSSIER,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environnement,
            )
        except OSError as erreur:
            self.afficher_erreur(str(erreur))
            return

        self.futur = self.tache.submit(self.processus.communicate)
        self.fenetre.after(100, self.verifier_detection)

    def verifier_detection(self):
        if not self.futur.done():
            self.fenetre.after(100, self.verifier_detection)
            return

        erreur = self.futur.exception()
        if erreur is not None:
            self.afficher_erreur(str(erreur))
            return

        sortie, _ = self.futur.result()
        if self.processus.returncode != 0:
            self.afficher_erreur(sortie.strip() or "Le script s'est arrêté avec une erreur.")
            return

        try:
            joueur = lire_geste(sortie)
        except ValueError as erreur:
            self.afficher_erreur(f"{erreur}\n\n{sortie.strip()}")
            return

        ordinateur = random.choice(GESTES)
        self.compteur.config(text=resultat_manche(joueur, ordinateur))
        self.instruction.config(text=f"Vous : {joueur}    |    Ordinateur : {ordinateur}")
        self.detail.config(text="Prêt pour une autre manche ?")
        self.bouton.config(text="Rejouer", state="normal")

    def afficher_erreur(self, texte):
        self.compteur.config(text="Détection impossible")
        self.instruction.config(text="Vérifiez la caméra et le script de détection.")
        self.bouton.config(text="Réessayer", state="normal")
        messagebox.showerror("Erreur de détection", texte, parent=self.fenetre)

    def fermer(self):
        if self.processus is not None and self.processus.poll() is None:
            self.processus.terminate()
        self.tache.shutdown(wait=False, cancel_futures=True)
        self.fenetre.destroy()


if __name__ == "__main__":
    fenetre = tk.Tk()
    Jeu(fenetre)
    fenetre.mainloop()