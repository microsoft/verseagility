import json
import sys
sys.path.append('./code')
import infer

infer.init()
tr = infer.run(json.dumps([{"subject":"", 
                    "body":"My Windows 7 PC has a blank screen after i re-installed it. Not even getting an error code. Can I have Bill Gates number, need help?! Microsoft should know better...",
                    "attachment":""
    }]))
json.dumps(tr)
print(tr)

# infer.init(local=True)
# tr = infer.run(json.dumps([{"subject":"", 
#                     "body":"Mein Windows Vista rechner will nicht mehr - ich kriege dauernd fehler meldungen. Ich wollte mir eh einen neuen kaufen, aber ich hab kein Geld. Kann Bill Gates mir helfen?",
#                     "attachment":""
#     }]))
#json.dumps(tr)
# print(tr)