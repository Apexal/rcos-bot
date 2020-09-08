from .constants import *
from typing import List, Dict, Optional
from csv import DictReader
import requests
import re


def generate_text_channel_name(name: str) -> str:
    '''Given a name, convert it into what its Discord text channel title would be.'''
    no_white_space = re.sub(r'\W+', ' ', name)
    stripped = no_white_space.strip()
    no_nonalphanum = re.sub(r'\s+', '-', stripped)
    lowercased = no_nonalphanum.lower()
    return lowercased


def get_all_channels() -> List:
    '''Get all channels on the server.'''
    response = requests.get(
        f'https://discordapp.com/api/guilds/{RCOS_SERVER_ID}/channels', headers=HEADERS)
    response.raise_for_status()
    return response.json()


def find_channel(name: str, channel_type: int, parent_id=None) -> Optional[Dict]:
    '''Find and return a channel with the given criteria or return None'''
    if channel_type == TEXT_CHANNEL:
        name = generate_text_channel_name(name)
    for channel in all_channels:
        if channel['type'] == channel_type and channel['name'] == name and channel['parent_id'] == parent_id:
            return channel
    return None


def add_channel(name: str, channel_type: int = TEXT_CHANNEL, topic: str = None, parent_id=None, perms=None) -> Dict:
    '''Add a channel or category to the server.'''
    response = requests.post(f'https://discordapp.com/api/guilds/{RCOS_SERVER_ID}/channels',
                             json={
                                 'name': name,
                                 'type': channel_type,
                                 'topic': topic,
                                 'parent_id': parent_id,
                                 'permission_overwrites': perms
                             },
                             headers=HEADERS
                             )
    response.raise_for_status()
    return response.json()


def add_channel_if_not_exists(name: str, channel_type: int = TEXT_CHANNEL, topic: str = None, parent_id=None, perms=None) -> Dict:
    '''Add a channel if it does not already exist.'''
    # See if channel exists
    channel = find_channel(
        name, channel_type=channel_type, parent_id=parent_id)

    if channel == None:
        channel = add_channel(name, channel_type=channel_type,
                              topic=topic, parent_id=parent_id, perms=perms)
        all_channels.append(channel)
        print(
            f'{CHANNEL_TYPES[channel["type"]]} "{channel["name"]}" was added')
    else:
        print(
            f'{CHANNEL_TYPES[channel["type"]]} "{channel["name"]}" already exists')
    return channel


def delete_channel(channel_id) -> Dict:
    response = requests.delete(f'https://discordapp.com/api/channels/{channel_id}',
                               headers=HEADERS
                               )
    response.raise_for_status()
    return response.json()


def get_all_roles() -> List:
    '''Get all roles on the server.'''
    response = requests.get(
        f'https://discordapp.com/api/guilds/{RCOS_SERVER_ID}/roles', headers=HEADERS)
    response.raise_for_status()
    return response.json()


def find_role(name) -> Optional[Dict]:
    '''Find a role and return it if it exists. Otherwise returns None.'''
    for role in all_roles:
        if role['name'] == name:
            return role
    return None


def add_role(name: str, hoist=False) -> Dict:
    '''Add a new role to the server.'''
    response = requests.post(
        f'https://discordapp.com/api/guilds/{RCOS_SERVER_ID}/roles', json={'name': name, 'hoist': hoist}, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def add_role_if_not_exists(name: str, hoist=False) -> Dict:
    '''Add a new role to the server if it doesn't exist. Returns the created or existing role.'''
    role = find_role(name)
    if role == None:
        role = add_role(name, hoist=hoist)
        all_roles.append(role)

    return role


all_channels = get_all_channels()
all_roles = get_all_roles()


def run():
    students = dict()
    small_groups = dict()

    with open('students.csv', 'r') as file:
        csv_reader = DictReader(file)
        for row in csv_reader:
            students[row['rcs_id']] = row

            if row['small_group'] not in small_groups:
                small_groups[row['small_group']] = set()

            small_groups[row['small_group']].add(row['project'])

    for small_group in small_groups:
        title = f'Small Group {small_group}'

        # Create role
        small_group_role = add_role_if_not_exists(title)

        # Create @everyone permission overwrites
        perms = [
            {
                'id': RCOS_SERVER_ID,
                'type': 'role',
                'deny': VIEW_CHANNELS
            },
            {
                'id': small_group_role['id'],
                'type': 'role',
                'allow': VIEW_CHANNELS
            }
        ]

        # Create category for small group to hold general and project channels
        small_group_category = add_channel_if_not_exists(
            title, CATEGORY, perms=perms)

        # Create this small group's general channels
        small_group_text_channel = add_channel_if_not_exists(
            title, parent_id=small_group_category['id'])
        small_group_voice_channel = add_channel_if_not_exists(
            title, channel_type=VOICE_CHANNEL, parent_id=small_group_category['id'])

        # Create this small group's project channels and roles
        for project in small_groups[small_group]:
            project_role = add_role_if_not_exists(project, hoist=True)
            project_perms = [
                {
                    'id': RCOS_SERVER_ID,
                    'type': 'role',
                    'deny': VIEW_CHANNELS
                },
                {
                    'id': project_role['id'],
                    'type': 'role',
                    'allow': VIEW_CHANNELS
                },
                {
                    'id': DISCORD_PM_ROLE_ID,
                    'type': 'role',
                    'allow': MANAGE_MESSAGES
                }
            ]
            project_text_channel = add_channel_if_not_exists(
                project, channel_type=TEXT_CHANNEL, topic=f'🗨️ Discussion channel for {project}', parent_id=small_group_category['id'], perms=project_perms)
            project_voice_channel = add_channel_if_not_exists(
                project, channel_type=VOICE_CHANNEL, parent_id=small_group_category['id'], perms=project_perms)