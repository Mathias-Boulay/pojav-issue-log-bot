import functions_framework
import requests
import re
import os


def get_latestlog_file(comment_body: str) -> str:
    latestlog_link = re.search(r'https://github\.com/PojavLauncherTeam/PojavLauncher/files/.*?/latestlog\.txt', comment_body)
    if not latestlog_link:
        return ""
    log_file = requests.get(latestlog_link.group(0)).text
    return log_file


def build_response_comment(parsed_json: dict) -> str:
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

    print(comment_content)
    return comment_content


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
    log_content = get_latestlog_file(body)

    # Send it to the parser
    parsed_json = requests.post('https://pojav-parser-function-3tx4ib7zya-uw.a.run.app', data=log_content).json()
    print(parsed_json)

    comment_json = {"body": build_response_comment(parsed_json)}
    token = "Bearer {}".format(os.environ.get('TOKEN_GITHUB'))
    comment_response = requests.post(data['comment']['issue_url'], headers={'Authorization': token}, json=comment_json)
    print(comment_response)
    print(comment_response.json())

    return {}
