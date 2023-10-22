import accessibility_events.database as db

class databaseInteractions:
    def getAllEvents(self):
        return list(db.Event.select().dicts())

    def getAllEmails(self):
        return list(db.EMailContent.select().dicts())
    
class searchInDataBase:
    def searchEvents(self, search):
        return list(db.Event.select().where((db.Event.title.contains(search)) | (db.Event.content.contains(search)) | (db.Event.date.contains(search)) | (db.Event.time.contains(search)) | (db.Event.location.contains(search)) | (db.Event.link.contains(search)) | (db.Event.tags.contains(search))).dicts())
    
    def searchEmails(self, search):
        return list(db.EMailContent.select().where(db.EMailContent.subject.contains(search)).dicts())
    


    
    