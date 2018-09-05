from src.data_import.csv_data import csv_import as csv_import
from src.data_import.json_data import json_import as json_import
from src.structures.thread import threatStructure

class dataImporter(threatStructure):

    def __init__(self,outputQueue,filename, realtime = True):

        super(dataImporter, self).__init__()
        self.target = self.run

        self.outputQueue = outputQueue
        self.filename = filename

        if self.filename[-3:] == 'csv':
            self.dataImport = csv_import(self.outputQueue,self.filename, realtime)
        else:
            self.dataImport = json_import(self.outputQueue,self.filename, realtime)

    def run(self):
        self.dataImport.start()
        self.active = False