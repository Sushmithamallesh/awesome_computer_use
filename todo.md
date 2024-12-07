# TODO
- Add a stop button to the Streamlit app
- I just want to send the one screenshot to claude. What nonsense is this sendind a bunch of them lol.Test if I am wrong





Checklist:
- [] Message to be sent properly
- [] Proper helicone integration
- [] Tools to be defined
- [] Get a single response from Claude
- [] Check the body you are sending to Claude
- [] Check the response you are getting from Claude
- [] All sort of optimisation look at the example directory look at everything
- [] What the heck is this?     """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """
- [] Add a stop button to the Streamlit app



Type management: 
UI Message (lightweight) 
  → Convert to Claude Message (API type)
  → API Call
  → Response
  → Convert back to UI Message (lightweight)

