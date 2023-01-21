import functions_framework
import requests
import re
import os


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
    data = request.json
    print(data)
    body = data['comment']['body']

    # get the log file
    latestlog_link = re.search(r'https://github\.com/PojavLauncherTeam/PojavLauncher/files/.*?/latestlog\.txt', body)
    if not latestlog_link:
        return {}
    log_file = requests.post(latestlog_link.group(0)).text
    print(log_file)

    # Send it to the parser
    parsed_json = requests.post('https://pojav-parser-function-3tx4ib7zya-uw.a.run.app', data=log_file).json()
    print(parsed_json)

    # Build the response string
    comment_content = "**Pojav version:** {0}-{1}-{2}-{3}\n\r".format(
        parsed_json['version']['major_code'], parsed_json['version']['commit_number'],
        parsed_json['version']['commit_short'], parsed_json['version']['branch'])
    comment_content += "**Architecture:** {}\n\r".format(parsed_json.get('architecture'))
    comment_content += "**Renderer:** {}\n\r".format(parsed_json['renderer'])
    comment_content += "**Minecraft version:** {0} - Type:{1}\n\r".format(
        parsed_json['minecraft_version']['name'], parsed_json['minecraft_version']['type'])
    comment_content += "**Java version:** {0} {1} {2}\n\r".format(
        parsed_json['java_runtime']['source'], parsed_json['java_runtime']['type'],
        parsed_json['java_runtime']['version'])
    comment_content += "**Errors detected:** \n\r"
    for error in parsed_json['errors']:
        comment_content += "\t{0}\n\r".format(error)

    comment_json = {"body": comment_content}
    token = "Bearer {}".format(os.environ.get('TOKEN_GITHUB'))
    comment_response = requests.post(data['comment']['issue_url'], auth=token, json=comment_json)
    print(comment_response)

    return {}
