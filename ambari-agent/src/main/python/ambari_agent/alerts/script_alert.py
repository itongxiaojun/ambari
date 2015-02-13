#!/usr/bin/env python

"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import imp
import logging
import os
import re
from alerts.base_alert import BaseAlert
from resource_management.core.environment import Environment
from symbol import parameters

logger = logging.getLogger()

class ScriptAlert(BaseAlert):
  def __init__(self, alert_meta, alert_source_meta, config):
    """ ScriptAlert reporting structure is output from the script itself """
    
    alert_source_meta['reporting'] = {
      'ok': { 'text': '{0}' },
      'warning': { 'text': '{0}' },
      'critical': { 'text': '{0}' },
      'unknown': { 'text': '{0}' }
    }
    
    super(ScriptAlert, self).__init__(alert_meta, alert_source_meta)
    
    self.config = config
    self.path = None
    self.stacks_dir = None
    self.common_services_dir = None
    self.host_scripts_dir = None
    self.path_to_script = None
    
    if 'path' in alert_source_meta:
      self.path = alert_source_meta['path']
      
    if 'common_services_directory' in alert_source_meta:
      self.common_services_dir = alert_source_meta['common_services_directory']

    if 'stacks_directory' in alert_source_meta:
      self.stacks_dir = alert_source_meta['stacks_directory']

    if 'host_scripts_directory' in alert_source_meta:
      self.host_scripts_dir = alert_source_meta['host_scripts_directory']
      
    # execute the get_tokens() method so that this script correctly populates
    # its list of keys
    try:
      cmd_module = self._load_source()
      tokens = cmd_module.get_tokens()
        
      # for every token, populate the array keys that this alert will need
      if tokens is not None:
        for token in tokens:
          # append the key to the list of keys for this alert
          self._find_lookup_property(token)
    except:
      logger.exception("[Alert][{0}] Unable to parameterize tokens for script {1}".format(
        self.get_name(), self.path))
              
    
  def _collect(self):
    cmd_module = self._load_source()
    if cmd_module is not None:
      # convert the dictionary from 
      # {'foo-site/bar': 'baz'} into 
      # {'{{foo-site/bar}}': 'baz'}
      parameters = {}
      for key in self.config_value_dict:
        parameters['{{' + key + '}}'] = self.config_value_dict[key]

      # try to get basedir for scripts
      # it's needed for server side scripts to properly use resource management
      matchObj = re.match( r'((.*)services\/(.*)\/package\/)', self.path_to_script)
      if matchObj:
        basedir = matchObj.group(1)
        with Environment(basedir, tmp_dir=self.config.get('agent', 'tmp_dir')) as env:
          return cmd_module.execute(parameters, self.host_name)
      else:
        return cmd_module.execute(parameters, self.host_name)
    else:
      return (self.RESULT_UNKNOWN, ["Unable to execute script {0}".format(self.path)])
    

  def _load_source(self):
    if self.path is None and self.stack_path is None and self.host_scripts_dir is None:
      raise Exception("The attribute 'path' must be specified")

    paths = self.path.split('/')
    self.path_to_script = self.path
    
    # if the path doesn't exist and stacks dir is defined, try that
    if not os.path.exists(self.path_to_script) and self.stacks_dir is not None:
      self.path_to_script = os.path.join(self.stacks_dir, *paths)

    # if the path doesn't exist and common services dir is defined, try that
    if not os.path.exists(self.path_to_script) and self.common_services_dir is not None:
      self.path_to_script = os.path.join(self.common_services_dir, *paths)

    # if the path doesn't exist and the host script dir is defined, try that
    if not os.path.exists(self.path_to_script) and self.host_scripts_dir is not None:
      self.path_to_script = os.path.join(self.host_scripts_dir, *paths)

    # if the path can't be evaluated, throw exception      
    if not os.path.exists(self.path_to_script) or not os.path.isfile(self.path_to_script):
      raise Exception(
        "Unable to find '{0}' as an absolute path or part of {1} or {2}".format(self.path,
          self.stacks_dir, self.host_scripts_dir))

    if logger.isEnabledFor(logging.DEBUG):
      logger.debug("[Alert][{0}] Executing script check {1}".format(
        self.get_name(), self.path_to_script))

          
    if (not self.path_to_script.endswith('.py')):
      logger.error("[Alert][{0}] Unable to execute script {1}".format(
        self.get_name(), self.path_to_script))

      return None

    return imp.load_source(self._find_value('name'), self.path_to_script)


  def _get_reporting_text(self, state):
    '''
    Always returns {0} since the result of the script alert is a rendered string.
    This will ensure that the base class takes the result string and just uses
    it directly.

    :param state: the state of the alert in uppercase (such as OK, WARNING, etc)
    :return:  the parameterized text
    '''
    return '{0}'
