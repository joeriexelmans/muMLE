import sys

def yes_no(msg: str):
   sys.stdout.write(f"{msg} <Y/n>")

   choice = input()
   if choice in {'Y','y',''}:
      return True
   elif choice in {'N','n'}:
      return False
   else:
      print("Please respond with 'y' or 'n'")
      return yes_no(msg)

def pause():
   print("press any key...")
   input()

def choose(msg:str, options):
   arr = []
   for i, (key, result) in enumerate(options):
      print(f"  {i}. {key}")
      arr.append(result)
   if len(arr) == 0:
      return
   return __choose(msg, arr)

def __choose(msg: str, arr):
   sys.stdout.write(f"{msg} ")
   try:
      raw = input()
      choice = int(raw) # may raise ValueError
      if choice >= 0 and choice < len(arr):
         return arr[choice]
   except ValueError:
      pass

   print("Invalid option")
   return __choose(msg, arr)
