def names():
    all_names = []

    def inner(name):
        all_names.append(name)
        return all_names
        
    
    return inner


boys = names()
print(boys("DAIM"))

print(boys("LAIM"))

girls = names()

print(girls("BOBA"))
print(girls("TOMA"))