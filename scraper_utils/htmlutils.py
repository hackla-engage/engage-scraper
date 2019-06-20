from bs4 import BeautifulSoup

def bs4_data_from_url(url, session, method, data=None):
    """
    Helper, common task
    """
    if method == "GET":
        r = session.get(url)
    else:
        r = session.post(url, data=data)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup

def parse_query_params(url):
    '''
    Takes the split key value pairs which are made up of ["key=value", "key=value", "key="]
    value may be empty except for MeetingID and ID keys
    Returns a dictionary with two keys "MeetingID" and "ID"
    Values are already split on &
    '''
    params = url.split("?")[1].strip().split("&")
    if len(params) == 0:
        raise IndexError
    query = dict()
    for param in params:
        split_param = param.split("=")
        query[split_param[0].strip()] = split_param[1].strip()
    return query

def check_style_special(inline_style_string):
    if "bold" in inline_style_string:
        return True
    if "underline" in inline_style_string:
        return True
    return False
