from PIL import Image
from fastapi import HTTPException
import secrets
from config.picture_drive import drive

async def uploadImageToDeta(image):
    with image.file as f:
        fileName = image.filename
        extensions = fileName.split(".")[1]
        if extensions not in ['png', 'jpg', 'jpeg']:
            raise HTTPException(
                status_code=400, 
                detail="file not allowed"
                )
        else :
            token_name = secrets.token_hex(10)+"."+extensions
            generated_name = token_name
            
            img = Image.open(f)
            image_width, image_height = img.size
            
            if image_width > 600 or image_height > 600 :
                # compress image
                max_image_size = (600, 600) 
                img.thumbnail(max_image_size)
                # Simpan gambar kedalam ByteIO
                from io import BytesIO
                compressed_image = BytesIO()
                extensions_upper = extensions.upper()
                if extensions_upper == 'jpg' or extensions_upper == 'JPG' :
                    img.save(compressed_image, format='JPEG')
                else :
                    img.save(compressed_image, format=extensions_upper)
                    
                compressed_image.seek(0)
                
                push_the_file = drive.put(generated_name[1:], compressed_image)
            else :
                # Simpan gambar kedalam ByteIO
                from io import BytesIO
                original_image = BytesIO()
                extensions_upper = extensions.upper()
                if extensions_upper == 'jpg' or extensions_upper == 'JPG' :
                    img.save(original_image, format='JPEG')
                else :
                    img.save(original_image, format=extensions_upper)
                    
                original_image.seek(0)
                
                push_the_file = drive.put(generated_name[1:], original_image)
        
        return push_the_file


