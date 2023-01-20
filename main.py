import functions_framework


@functions_framework.http
def handle_request(request):
    """
        HTTP Cloud Function that declares a variable.
        Args:
            request (flask.Request): The request object.
            <https://flask.palletsprojects.com/en/latest/api/>
        Returns:
            The response text, or any set of values that can be turned into a
            Response object using `make_response`
            <https://flask.palletsprojects.com/en/latest/api/>.
        """
    print(request.data)
    return {}
