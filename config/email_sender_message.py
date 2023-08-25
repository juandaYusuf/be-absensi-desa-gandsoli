import smtplib
from email.message import EmailMessage



#! MEMBUAT SISTEMATIS MENGIRIM NOTIFIKASI KE EMAIL 
class EmailSender():
    def __init__(self, reciver_email : str, reciver_name : str, reciver_presence_status : str, description:str, date : str) :
        self.reciver_email = reciver_email
        self.reciver_name=reciver_name
        self.reciver_presence_status=reciver_presence_status
        self.description=description
        self.date=date
        
    def sender(self):
        
        def _htmlContent():
            content = None
            with open('./assets/message/content_email_message.html', 'r') as file:
                content = file.read()
            return content
        
        
        content_msg = _htmlContent()
        fill_data = content_msg.format(
            reciver_name=self.reciver_name,
            reciver_presence_status=self.reciver_presence_status,
            description=self.description,
            date=self.date
            )
        user_email_reciver = self.reciver_email
        email_address_sender = "desa.gandasoli.pld@gmail.com" 
        email_password_sender = "qhvesdqutvsqstxp" 
        
        msg = EmailMessage()
        msg['Subject'] = f"PEMBERITAHUAN STATUS KEHADIRAN"
        msg['From'] = email_address_sender
        msg['To'] = user_email_reciver
        
        
        msg.add_alternative(fill_data, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address_sender, email_password_sender)
            smtp.send_message(msg)
        
        # return fill_data



class ConfirmEmailSender():
    def __init__(self, reciver_email : str, reciver_name : str, verify_code: int) :
        self.reciver_email = reciver_email
        self.reciver_name=reciver_name
        self.verify_code=verify_code
        
    def sender(self):
        
        def _htmlContent():
            content = None
            with open('./assets/message/verify.html', 'r') as file:
                content = file.read()
            return content
        
        
        content_msg = _htmlContent()
        fill_data = content_msg.format(
            reciver_name=self.reciver_name,
            email=self.reciver_email,
            verfycode=self.verify_code
            )
        user_email_reciver = self.reciver_email
        email_address_sender = "panjoelalfath@gmail.com" 
        email_password_sender = "huqhxkztjwmsbvlx" 
        
        msg = EmailMessage()
        msg['Subject'] = f"PEMBERITAHUAN VERIFIKASI KODE"
        msg['From'] = email_address_sender
        msg['To'] = user_email_reciver
        
        
        msg.add_alternative(fill_data, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address_sender, email_password_sender)
            smtp.send_message(msg)
        
        print(f'Email verification code has been sent to {self.reciver_email}')
        # return fill_data
