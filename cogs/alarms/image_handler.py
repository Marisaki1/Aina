import os

class ImageHandler:
    IMAGE_FOLDER = "assets/images/alarms/"

    def __init__(self):
        if not os.path.exists(self.IMAGE_FOLDER):
            os.makedirs(self.IMAGE_FOLDER)

    def save_image(self, file, filename):
        path = os.path.join(self.IMAGE_FOLDER, filename)
        with open(path, "wb") as f:
            f.write(file)
        return path
