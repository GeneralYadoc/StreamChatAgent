import time
import threading
import queue
import pytchat

class StreamChatAgent:
  def __init__( self,
                video_id,
                get_item_cb,
                pre_filter_cb=None,
                post_filter_cb=None,
                max_queue_size=0,
                interval_sec=0.001 ):
    self.get_item_cb = get_item_cb
    self.pre_filter_cb = pre_filter_cb
    self.post_filter_cb = post_filter_cb
    self.item_queue = queue.Queue(max_queue_size)
    self.interval_sec = interval_sec
    self.alive = False

    self.chat = pytchat.create(video_id=video_id)

    self.my_put_thread = threading.Thread(target=self.put_items)
    self.my_get_thread = threading.Thread(target=self.get_items)

  def connect(self):
    self.alive = True
    self.my_put_thread.start()
    self.my_get_thread.start()
    self.my_get_thread.join()
    self.my_put_thread.join()

  def disconnect(self):
    self.alive = False

  def is_chat_alive(self, immediate=False, retry_count=5, sleep=1.0):
    if immediate:
      retry_count=1
    i = 0
    while True:
      if not self.alive:
        return False
      if self.chat.is_alive():
        return True
      i += 1
      if retry_count > 0 and i >= retry_count:
        return False
      time.sleep(sleep)

  def put_items(self):
    while self.alive and self.is_chat_alive():
      for c in self.chat.get().sync_items():
        if not self.alive:
          break
        prefiltered_c = c
        if self.pre_filter_cb:
          prefiltered_c =  self.pre_filter_cb(c)
        if prefiltered_c:
          if self.item_queue.full():
            self.item_queue.get()
          self.item_queue.put(prefiltered_c)

  def get_items(self):
    while self.alive and self.is_chat_alive():
      while self.alive and not self.item_queue.empty():
        c = self.item_queue.get()
        postfiltered_c = c
        if self.post_filter_cb:
          postfiltered_c = self.post_filter_cb(c)
        if postfiltered_c:
          self.get_item_cb(postfiltered_c)
      time.sleep(self.interval_sec)
