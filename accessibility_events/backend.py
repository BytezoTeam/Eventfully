from .database import *

class db:
    def getAllEvents(self):
        return list(Event.select().dicts())

    def getAllEmails(self):
        return list(EMailContent.select().dicts())
    
class searchInDataBase:
    def searchEvents(self, search):
        return list(Event.select().where((Event.title.contains(search)) | (Event.content.contains(search)) | (Event.date.contains(search)) | (Event.time.contains(search)) | (Event.location.contains(search)) | (Event.link.contains(search)) | (Event.tags.contains(search))).dicts())
    
    def searchEmails(self, search):
        return list(EMailContent.select().where(EMailContent.subject.contains(search)).dicts())
    


    
    