#!/usr/bin/env python3
"""Photo bot app.
"""
import json
import os.path
import pprint 
from threading import Thread
import time
import sys

import twilio_mms
import picamera
from wuw import sample_client as mix_client

class Photobot(Thread):
    """Photobot

    Take photos by voice and natural language understanding.

    """
    IDLE = 1
    WAITING_PHONE_NUMBER = 2
    WAITING_DELAY_TIME = 3
    GREETINGS = {
        IDLE: "I'm ready to take your photo.",
        WAITING_PHONE_NUMBER: "I'm still waiting for your phone number.",
        WAITING_DELAY_TIME: "I'm still waiting for the delay time."
    }

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        
        mix_client.mix_init("M4421_A2115_4") 
        self.listening = False
        self.__state = Photobot.IDLE

        self.__stop = False
        self.__alive = False
    
    def process_recognition_state(self, message):
        if message['state'] == 'listening_for_speech':
            spoken_text = None
            intent = None
            self.listening = True
        elif message['state'] == 'processing_speech':
            mix_client.send_message('/output/file', {
                    'path': mix_client.get_sound_path('processing.pcm')})
            self.listening = False
        elif message['state'] == 'waiting_for_wakeup':
            if self.listening:
                mix_client.send_message('/output/file', {
                    'path': mix_client.get_sound_path('timeout.pcm')})
            self.listening = False

    def process_recognition_result(self, message):
        spoken_text = message.get('transcriptions', [None])[0]
        if spoken_text is not None:
            mix_client.send_message('/output/synthesize', {
                'text': 'You said %s' % (spoken_text,)})
        else:
            mix_client.send_message('/output/file', {
                'path': mix_client.get_sound_path('no_utt.pcm')})
    
    def process_understanding_result(self, message):
        intent = message.get('nlu_interpretation_results',{}).get('payload',{}) \
                    .get('interpretations',[{}])[0].get('action',{})\
                    .get('intent',{}).get('value')
        if intent is not None:
            concepts = message.get('nlu_interpretation_results', {})\
                    .get('payload', {}).get('interpretations', [{}])[0]\
                    .get('concepts', {})

            if intent == "TAKE_PHOTO":
                mix_client.send_message('/output/synthesize', {
                    'text': "Sure, what's your phone number?"})
                self.__state = Photobot.WAITING_PHONE_NUMBER

            elif intent == "OFFER_PHONE_NUMBER":
                if concepts:                                                            
                    phone_number_fields = concepts.get('PHONE_NUMBER')                  
                    if phone_number_fields:                                             
                        self.phone_num = phone_number_fields[0].get('literal')\
                            .replace('-','')

                        mix_client.send_message('/output/synthesize', {
                            'text': "Great, how long would you like to delay?"})
                        self.__state = Photobot.WAITING_DELAY_TIME
                    else:
                        mix_client.send_message('/output/synthesize', {
                            'text': "Sorry, your phone number, please"})
                else:
                    mix_client.send_message('/output/synthesize', {
                        'text': "Sorry, your phone number, please"})

            elif intent == "OFFER_WAITING_TIME" or (intent == "NO_INTENT" and 
                    self.__state == Photobot.WAITING_DELAY_TIME):
                nuance_duration_fields = concepts.get('nuance_DURATION')            
                if nuance_duration_fields:                                          
                    waiting_time_literal = nuance_duration_fields[0].get('literal') 
                    self.waiting_delay = mix_client.normalize_duration(
                            nuance_duration_fields[0])
                    # -$- Now take picture and send it to your phone -$-
                    mix_client.send_message('/output/synthesize', {
                        'text': "Now wait for {} seconds and say Cheese."\
                            .format(self.waiting_delay)
                    })
                    photo = picamera.take_photo(self.waiting_delay)
                    twilio_mms.send_photo(self.phone_num, photo.url, True)
                    photo.delete()
                    self.phone_num = None
                    self.waiting_delay = 0
                    self.__state = Photobot.IDLE

                    mix_client.send_message('/output/synthesize', {
                        'text': "Awesome, photo has been sent to you"})
                else:
                    mix_client.send_message('/output/synthesize', {
                        'text': "Sorry, how long?"})

            elif intent == "CANCEL_PHOTO":
                mix_client.send_message('/output/synthesize', {
                        'text': "Okay, see you next time."})
                self.phone_num = None
                self.waiting_delay = 0
                self.__state = Photobot.IDLE
            
            elif intent == "GREETING_ASK":
                response_greeting = "Thanks for asking, " + Photobot.GREETINGS[self.__state]
                mix_client.send_message('/output/synthesize', {
                    'text': response_greeting}) 

            elif intent == "NO_INTENT":
                mix_client.send_message('/output/synthesize', {
                    'text': "Sorry, what's that?"})
            else:
                mix_client.send_message('/output/synthesize', {
                    'text': "Hmm, please say it again?"})

            # -$- Play indication sound -$-
            if intent == 'NO_MATCH':
                mix_client.send_message('/output/file', {
                    'path': mix_client.get_sound_path('no_nlu.pcm')})
            else:
                mix_client.send_message('/output/file', {
                    'path': mix_client.get_sound_path('success.pcm')})
        else:
            mix_client.send_message('/output/file', {
                'path': mix_client.get_sound_path('no_nlu.pcm')})

    def run(self):
        """Photobot loop"""

        self.__alive = True
        while not self.__stop:
            # -$-TODO: get_message will block the exit even we call stop() -$-
            message = mix_client.get_message()
            if message is None:
                break
            pprint.pprint(message)

            if message['event'] == 'recognition_state':
                self.process_recognition_state(message)
            elif message['event'] == 'recognition_result':
                self.process_recognition_result(message)        
            elif message['event'] == 'understanding_result':
                self.process_understanding_result(message)

        self.__alive = False

    def stop(self):
        """Stop photo bot."""
        self.__stop = True

    @property
    def alive(self):
        """Property to test bot is alive."""
        return self.__alive

if __name__=="__main__":
    photobot = Photobot()
    photobot.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        photobot.stop()
        print("Bye photobot!")
        


