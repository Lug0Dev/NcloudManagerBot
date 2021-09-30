#Desarrollando Ncloud Manager



import owncloud
from telegram.ext import Updater, CommandHandler, ConversationHandler,CallbackQueryHandler ,MessageHandler, Filters
from telegram import InlineKeyboardMarkup,InlineKeyboardButton

cloud=owncloud.Client('https://autocloud.cujae.edu.cu')

#========================================Funciones===============================================

def start(update,context):
    update.message.reply_text(text='El bot esta en fase de desarrollo todavía, por lo que esta corriendo bajo comandos, proximamente se le agregarán botones interactivos',
    reply_markup=InlineKeyboardMarkup([

        [InlineKeyboardButton(text='✅Página de inicio✅',url='https://autocloud.cujae.edu.cu')]
        ]))


def login_ncloud(update,context):  
    update.message.reply_text('⌛Iniciando sesion...⌛')
    try:
        cloud.login('abharold.l','AB00012862329*2021')
        update.message.reply_text('✅Sesión iniciada correctamente✅')
    except:
        update.message.reply_text('🚨Error al iniciar sesión🚨')

def logout_ncloud(update,context):
    cloud.logout()
    update.message.reply_text('❌Sesión cerrada❌')

def crear_carpetas(update,context):
    
    pass        
    
    


if __name__=='__main__':
    
    updater=Updater(token='1966004551:AAHG_waNpVHUs8aCPiRIo8qE37kO_f9cgRI', use_context=True)
    dp=updater.dispatcher

#=======================================Handlers===================================================

    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(CommandHandler('login',login_ncloud))
    dp.add_handler(CommandHandler('logout',logout_ncloud))
    
    
#=======================================Arrancada====================================================      
    updater.start_polling()
    print('El bot esta en funcionamiento')
    updater.idle()
    
