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

