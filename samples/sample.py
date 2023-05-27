import sys
import re
import StreamChatAgent as sca  # Import this.

# callback for getting YouTube chat items
# You can implement several processes in it.
# This example prints datetime, ahthor name, message, of each item.
def get_item_cb(c):
  print(f"{c.datetime} [{c.author.name}]- {c.message}")

# pre putting queue filter
# You can edit YouTube chat items before putting internal queue.
# You can avoid putting internal queue by returning None.
# This example removes items whose message consists of stamps only.
def pre_filter_cb(c):
  return None if re.match(r'^(:[^:]+:)+$', c.message) else c

# post getting queue filter
# You can edit YouTube chat items after popping internal queue.
# You can avoid sending items to get_item_cb by returning None.
# This example removes stamps from message of items.
def post_filter_cb(c):
  c.message = re.sub(r':[^:]+:','', c.message)
  return c

# Video ID is given from command line in this example.
if len(sys.argv) <= 1:
  exit(0)

# Create StreamChatAgent instance.
params = sca.params(
  video_id = sys.argv[1],
  get_item_cb = get_item_cb,
  pre_filter_cb = pre_filter_cb,
  post_filter_cb = post_filter_cb
)
agent = sca.StreamChatAgent( params )

# Start async getting YouTube chat items.
# Then get_item_cb is called continuosly.
agent.start()

# Wait any key inputted from keyboad.
input()

# Finish getting items.
# Internal thread will stop soon.
agent.disconnect()

# Wait terminating internal threads.
agent.join()

del agent

