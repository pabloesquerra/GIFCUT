# -*- coding: utf-8 -*-
# USAGE

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import datetime
from flask import Response
from flask import render_template
import threading
import argparse
import time
import cv2
import numpy as np
import asyncio
import datetime
import random
from computervision.filtros import rotate_bound
from computervision.filtros import resize_video
from servicios.web import Cliente
import os 
from werkzeug.utils import secure_filename
import copy
from flask import send_file, send_from_directory
#UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'png', 'jpg', 'jpeg', 'gif'}
n=0
def generar_track_slider(id):
    step = int(len(Clientes[id].frames)/10)
    dsize=(100,77)
    track=list()
    for i in range(0,len(Clientes[id].frames),step):
        scaled = cv2.resize(Clientes[id].frames[i], dsize, interpolation = cv2.INTER_CUBIC) 
        track.append(scaled)
    Clientes[id].slider = cv2.hconcat([track[0], track[1], track[2], track[3], track[4], track[5], track[6], track[7], track[8], track[9]])
    #cv2.imwrite('static/Track.png', h_img, )
    

def leer_video(filename, id):
    global marco
    borderType = cv2.BORDER_CONSTANT
    #print(datetime.datetime.now())
    frames = cv2.VideoCapture('uploads/'+str(filename))
    frames.set(3, 320)
    frames.set(4,240)
    #print(datetime.datetime.now())
    # Check if camera opened successfully
    if (frames.isOpened()== False): 
        print("Error opening video stream or file")
    # Read until video is completed
    width = frames.get(3)
    height = frames.get(4)
    fps = frames.get(5)
    if width > height:
        scale = 640 /width
        dsize = (int(width*scale), int(height*scale))
    else:
        scale = 480 /height
        
        dsize = (int(width*scale), int(height*scale))
    
    while(frames.isOpened()):
        ret, frame = frames.read()
        if ret == True:
            scaled = cv2.resize(frame, dsize, interpolation = cv2.INTER_CUBIC)     
            Clientes[id].frames.append(scaled)
        
        if ret == False:
            break
    Clientes[id].end = len(Clientes[id].frames)-1
    generar_track_slider(id)

def generarId(identificadorUnico):
    identificadorUnico += 1
    return identificadorUnico

def control_motion():
    # grab global references to the video stream, output frame, and
    # lock variables
    global Clientes
    
    # loop over frames from the frame files
    while True:

        for cliente in Clientes:  
            if cliente.playPause==1:
                if cliente.nroFrame < cliente.end: 
                    cliente.nroFrame += 1
                    cliente.track = int(cliente.nroFrame * 1000 / len(cliente.frames))
                elif cliente.nroFrame >= cliente.end:#reinicia
                    cliente.nroFrame = cliente.start
                        
        time.sleep(0.04)   

def video_player(id):
    # grab global references to the output frame and lock variables
    global lock, Clientes, n    
    # loop over frames from the output stream
    while True: 
       
        if Clientes[id].nroFrame != Clientes[id].lastFrame or Clientes[id].update: #sólo actualizo si cambió el frame a mostrar
            Clientes[id].lastFrame = Clientes[id].nroFrame 
            Clientes[id].update = False
            frame = Clientes[id].frames[Clientes[id].nroFrame]
            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            with lock:
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')	

def dibujar_sombra_izq(id, img):
    xi, yi, wi, hi = 0, 0, int(Clientes[id].start * 1000 / len(Clientes[id].frames)), 100
    #sombra izquierda
    sub_img = img[yi:yi+hi, xi:xi+wi]
    white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255
    res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)
    img[yi:yi+hi, xi:xi+wi] = res
    return img

def dibujar_sombra_der(id, img):
    xf, yf, wf, hf = 1000, 0, int(1000 - (Clientes[id].end * 1000 / len(Clientes[id].frames))), 100
    #print(xf, yf, wf, hf)
    sub_img = img[yf:yf+hf, xf-wf:xf]
    white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255
    res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)
    img[yf:yf+hf, xf-wf:xf] = res
    return img

def slider_player(id):
    # grab global references to the output frame and lock variables
    global lock, marco, Clientes, n    
    # loop over frames from the output stream
    
    while True: 
        if Clientes[id].track != Clientes[id].lastTrack or Clientes[id].update: #sólo actualizo si cambió el frame a mostrar
            Clientes[id].lastTrack = Clientes[id].track 
            Clientes[id].update = False
        
            slider_img = copy.copy(Clientes[id].slider)
            cv2.line(slider_img,(Clientes[id].track,0),(Clientes[id].track,100),(0,0,255),3)
            slider_img = dibujar_sombra_izq(id=id, img=slider_img)
            slider_img = dibujar_sombra_der(id=id, img=slider_img)
            (flag, encodedImage) = cv2.imencode(".jpg", slider_img)
            with lock:
                yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')	
            time.sleep(.04)



# initialize a flask object
app = Flask(__name__, static_folder='static')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/downloads", methods=['GET'])
def downloads():
    global Clientes
    id = request.args.get('a', 0, type=int)
    filename = "project1.avi"
    return True #send_from_directory(app.static_folder, filename, as_attachment=True)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #return redirect(url_for('uploads', filename=filename))
            return render_template("video.html")
    return 

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")

@app.route("/video", methods=['GET', 'POST'])
def video():
    global identificadorUnico, listaClientes
    if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                #return redirect(url_for('uploads', filename=filename))
                identificadorUnico = generarId(identificadorUnico)
                leer_video(filename, id=identificadorUnico)
                Clientes[identificadorUnico].end = len(Clientes[identificadorUnico].frames)-1
                return render_template("video.html", unic_Id= str(identificadorUnico))

    return #render_template("video.html", unic_Id= str(identificadorUnico))

@app.route('/track_slider', methods=['GET'])
def track_slider():
    global Clientes
    i = request.args.get('a', 0, type=int)
    id = request.args.get('id', 0, type=int)
    Clientes[id].nroFrame = i
    Clientes[id].update = True
    return jsonify(result=i)
@app.route('/slider_position', methods=['GET'])
def slider_position():
    global Clientes
    id = request.args.get('id', 0, type=int)
    x = request.args.get('posX', 0, type=int)
    Clientes[id].nroFrame = int(x * len(Clientes[id].frames) / 1000)
    print('x= ', Clientes[id].nroFrame)
    Clientes[id].update = True
    return jsonify(result=True)

@app.route('/play', methods=['GET'])
def play():
    global Clientes
    #se recibe el id y se cambia el estado de playPause
    id = request.args.get('a', 0, type=int)
    Clientes[id].togglePlayPause()
    return  jsonify(True) #le tuve que poner un return NO VACIO para que no diera error

@app.route('/plus_one', methods=['GET'])
def plus_one():
    global Clientes
    #se recibe el id y se suma 1 a 
    id = request.args.get('a', 0, type=int)
    Clientes[id].nroFrame +=1
    Clientes[id].track = int(Clientes[id].nroFrame * 1000 / len(Clientes[id].frames))
    return  jsonify(result=Clientes[id].nroFrame)

@app.route('/minus_one', methods=['GET'])
def minus_one():
    global Clientes
    #se recibe el id y se resta 1 a 
    id = request.args.get('a', 0, type=int)
    Clientes[id].nroFrame -= 1
    Clientes[id].track = int(Clientes[id].nroFrame * 1000 / len(Clientes[id].frames))
    return  jsonify(result=Clientes[id].nroFrame) 

@app.route('/mark_start', methods=['GET'])
def mark_start():
    global Clientes
    id = request.args.get('a', 0, type=int)
    Clientes[id].start = Clientes[id].nroFrame
    Clientes[id].track = int(Clientes[id].nroFrame * 1000 / len(Clientes[id].frames))
    return  jsonify(True) 

@app.route('/mark_end', methods=['GET'])
def mark_end():
    global Clientes
    id = request.args.get('a', 0, type=int)
    Clientes[id].end = Clientes[id].nroFrame
    Clientes[id].nroFrame = Clientes[id].start
    return  jsonify(True) 

@app.route("/video_feed/<id>", methods=['GET'])
def video_feed(id):
    id=int(id)
    Clientes[id].nroFrame = 1
    Clientes[id].playPause = 1
    return Response(video_player(id), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route("/slider_feed/<id>", methods=['GET'])
def slider_feed(id):
    id=int(id)
    return Response(slider_player(id), mimetype = "multipart/x-mixed-replace; boundary=frame")


# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing the stream)
lock = threading.Lock()

# initialize variables globales
Clientes = [ Cliente() for i in range(10)]
identificadorUnico=0

if __name__ == '__main__':
    # start a thread that will perform motion control of the frames
    t1 = threading.Thread(target=control_motion)
    t1.daemon = True
    t1.start()
    app.config['UPLOAD_FOLDER'] = "./UPLOAD_FOLDER"
    # start the flask app
    app.run()
   
