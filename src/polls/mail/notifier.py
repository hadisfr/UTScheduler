class Notifier:
    def __init__(self, mail):
        self.mail = mail

    subject = "UTScheduler"

    @staticmethod
    def create_email_message(url):
        return "you are involved in a poll:\n" + url

    def notify_participate(self, owner, participate, url):
        message = Notifier.create_email_message(url)
        self.mail.send_email(Notifier.subject, message, owner.email, participate.email)
