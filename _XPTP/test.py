 
def runMatch(user):
 
    # match statement starts here .
    match user:
        case "Om":
            print("Om do not have access  to the database \
            only for the api code.")
        case "Vishal":
            print(
                "Vishal do not have access to the database , \
                only for the frontend code.")
 
        case "Rishabh":
            print("Rishabh have the access to the database")
            print("provideAccess Rishabh")
 
        case _:
            print("You do not have any access to the code")
 
 
if __name__ == "__main__":
    runMatch("Om")
    runMatch("Vishal")
    runMatch("Rishabh")
    runMatch("Coussini")