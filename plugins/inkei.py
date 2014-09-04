from util import hook

@hook.command('inkei')
@hook.command
def inkei(inp):
    '''.inkei <analyzer> [<mode>] <arguments> -- compares penis, tits, vagina, anus'''
    analyzer = inp.split(' ')[0]
    arguments = inp.split(' ')[1:]
    url = "http://en.inkei.net/"
    dateString = "!06660420"

    if (not analyzer) or (not arguments):
        return 'No arguments or no analyzer'
    elif(analyzer == 'penis' or analyzer == 'Penis'):
        if len(arguments) > 4:
            return "Too many dicks on the dance floor"
        elif len(arguments) == 1:
            return url + arguments[0]
        else:
            url += arguments[0]
            for word in arguments[1:]:
                 url += '!' + word
            return url
    elif(analyzer == 'tits' or analyzer == 'Tits'):
        url += "tits/"
        if len(arguments) > 4:
            return "Too many tits"
        elif len(arguments) == 1:
            return url + arguments[0]
        else:
            url += arguments[0]
            for word in arguments[1:]:
                 url += '!' + word
            return url                 
    elif(analyzer == 'vagina' or analyzer == 'Vagina'):
        mode = arguments[0]
        vagArgs = arguments[1:]
        url += "vagina/"
                 
        if not vagArgs:
            return "Need at least one argument"
        elif (mode == 'analyze' or mode == 'Analyze'):
            if len(vagArgs) > 4:
                return "Too many vaginas"
            elif len(vagArgs) == 1:
                return url + vagArgs[0]
            else:
                url += vagArgs[0]
                for word in vagArgs[1:]:
                     url += '!' + word
                return url
        elif (mode == 'affinity' or mode == 'Affinity'):
            url += 'a/'
            if len(vagArgs) != 2:
                return 'Need 2 arguments'
            else:
                return url + vagArgs[0] + '!' + vagArgs[1] + dateString
        else:
            return "Not a valid mode"
    elif(analyzer == 'anus' or analyzer == 'Anus'):
        mode = arguments[0]
        anusArgs = arguments[1:]
        url += "anus/"
                 
        if not anusArgs:
            return "Need at least one argument"
        elif (mode == 'analyze' or mode == 'Analyze'):
            if len(anusArgs) > 4:
                return "Too many anuses!"
            elif len(anusArgs) == 1:
                return url + anusArgs[0]
            else:
                url += anusArgs[0]
                for word in anusArgs[1:]:
                     url += '!' + word
                return url
        elif (mode == 'affinity' or mode == 'Affinity'):
            url += 'a/'
            if len(anusArgs) != 2:
                return 'Need 2 arguments'
            else:
                return url + anusArgs[0] + '!' + anusArgs[1] + dateString
        else:
            return "Not a valid mode"
    else:
        return "Not a valid analyzer"

