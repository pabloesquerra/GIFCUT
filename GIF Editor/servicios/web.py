class Cliente:
    nroClientes = 0
    def __init__(self):
        self.frames = list()
        self.slider = list()
        self.track = 0
        self.lastTrack = -1
        self.start = 0
        self.end = 0
        self.playPause = 0
        self.nroFrame = 0
        self.update = True
        self.angle = 0
        self.colortracking = False
        self.faceDetection = False
        self.lastFrame =- 1
        Cliente.nroClientes += 1
    
    def rotate(self):
        self.nroFrame = nroFrame

    def togglePlayPause(self):
        if self.playPause==0:
            self.playPause=1
        elif self.playPause==1:
            self.playPause=0
    
    def toggleColorTraking(self):
        if self.colortracking==0:
            self.colortracking=1
        elif self.colortracking==1:
            self.colortracking=0

    def toggleFaceDetection(self):
        if self.faceDetection==0:
            self.faceDetection=1
        elif self.faceDetection==1:
            self.faceDetectiong=0