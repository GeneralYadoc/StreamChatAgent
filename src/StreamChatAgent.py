import time
import threading
import queue
import math
import pytchat
from typing import Callable
from dataclasses import dataclass

@dataclass
class params:
  video_id: str
  get_item_cb: Callable[[any,],None]
  pre_filter_cb: Callable[[any,],any] = None
  post_filter_cb: Callable[[any,],any] = None
  max_queue_size: int = 1000
  interval_sec: float = 0.01

class StreamChatAgent(threading.Thread):
  def __init__( self, params ):
    self.__get_item_cb = params.get_item_cb
    self.__pre_filter_cb = params.pre_filter_cb
    self.__post_filter_cb = params.post_filter_cb
    self.__item_queue = queue.Queue(params.max_queue_size)
    self.__interval_sec = params.interval_sec
    self.__keeping_connection = False

    self.__chat = pytchat.create(video_id=params.video_id)

    self.__my_put_thread = threading.Thread(target=self.__put_items)
    self.__my_get_thread = threading.Thread(target=self.__get_items)

    super(StreamChatAgent, self).__init__(daemon=True)

  def connect(self):
    self.start()
    self.join()

  def run(self):
    self.__keeping_connection = True
    self.__my_put_thread.start()
    self.__my_get_thread.start()
    self.__my_get_thread.join()
    self.__my_put_thread.join()

  def disconnect(self):
    self.__keeping_connection = False

  def __is_alive(self, immediate=True, wait_sec=0):
    if not self.__my_get_thread.is_alive() and not self.__my_put_thread.is_alive():
      return False
    
    retry_count = math.floor(wait_sec / 0.01)
    if immediate:
      retry_count=1
    
    steps = 0 if retry_count == 0 else 1
    i = 0
    while True:
      if not self.__keeping_connection:
        return False
      if self.__chat.is_alive():
        return True
      i += steps
      if retry_count != 0 and i >= retry_count:
        return False
      time.sleep(0.01)

  def __put_items(self):
    start_time = time.time()
    while self.__is_alive(immediate=False):
      for c in self.__chat.get().sync_items():
        if not self.__keeping_connection:
          break
        prefiltered_c = c
        if self.__pre_filter_cb:
          prefiltered_c =  self.__pre_filter_cb(c)
        if prefiltered_c:
          if self.__item_queue.full():
            self.__item_queue.get()
          self.__item_queue.put(prefiltered_c)
      self.__sleep_from(start_time)
      start_time = time.time()
    self.__keeping_connection = False


  def __get_items(self):
    start_time = time.time()
    while self.__is_alive(immediate=False):
      while self.__keeping_connection and not self.__item_queue.empty():
        c = self.__item_queue.get()
        postfiltered_c = c
        if self.__post_filter_cb:
          postfiltered_c = self.__post_filter_cb(c)
        if postfiltered_c:
          self.__get_item_cb(postfiltered_c)
      self.__sleep_from(start_time, 0.01)
      start_time = time.time()
    self.__keeping_connection = False

  def __sleep_from(self, start_time, interval_sec=None):
    if not interval_sec:
      interval_sec = self.__interval_sec
    cur_time = time.time()
    sleep = interval_sec - (cur_time - start_time)
    if sleep > 0.:
      sleep_counter = math.floor(sleep * 10)
      sleep_frac = sleep - (sleep_counter / 10.)
      for i in range(sleep_counter):
        if not self.__keeping_connection:
          break
        time.sleep(0.1)
      time.sleep(sleep_frac)
