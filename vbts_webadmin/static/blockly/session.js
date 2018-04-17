//Blockly.Lua = Blockly.Generator.get('Lua');


//SESSION READY
Blockly.Blocks['session_ready'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:ready()");
    this.setOutput(true, "Boolean");
    this.setColour(65);
    this.setTooltip('checks whether the session is still active (true anytime between call starts and hangup). Returns TRUE or FALSE');
  }
};


Blockly.Lua['session_ready'] = function(block) {
  var code = 'session:ready()';
  // TODO: Change ORDER_NONE to the correct strength.
  return [code, Blockly.Lua.ORDER_FUNCTION_CALL];
};


//SESSION ANSWER
Blockly.Blocks['session_answer'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:answer()");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('Answers the session.');
  }
};


Blockly.Lua['session_answer'] = function(block) {
  var code = 'session:answer();\n';
  // TODO: Change ORDER_NONE to the correct strength.
  return [code, Blockly.Lua.ORDER_NONE];
};


//SESSION SLEEP
Blockly.Blocks['session_sleep'] = {
  init: function() {
    this.appendValueInput("s")
        .setCheck("Number")
        .appendField("session:sleep(seconds)");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('Sleeps/Pauses for the specified milliseconds.');
  }
};


Blockly.Lua['session_sleep'] = function(block) {
  var value_s = 1000 * Blockly.Lua.valueToCode(block, 's', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:sleep(' + value_s + ');\n';
  return code;
};


//SESSION STREAMFILE
Blockly.Blocks['session_streamfile'] = {
  init: function() {
    this.appendValueInput("filename")
        .setCheck("String")
        .appendField("session:streamFile");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('Stream a file endless to the session');
  }
};

Blockly.Lua['session_streamfile'] = function(block) {
  var value_filename = Blockly.Lua.valueToCode(block, 'filename', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:streamFile(' + value_filename + ');\n';
  return code;
};

//SESSION EXECUTE
Blockly.Blocks['session_execute'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:execute");
    this.appendValueInput("app")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("app");
    this.appendValueInput("data")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("data");
    this.setInputsInline(false);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('Executes a FS application. Requires app name and data arguments.');
  }
};


Blockly.Lua['session_execute'] = function(block) {
  var value_app = Blockly.Lua.valueToCode(block, 'app', Blockly.Lua.ORDER_ATOMIC);
  var value_data = Blockly.Lua.valueToCode(block, 'data', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:execute(' + value_app + ',' + value_data + ');\n';
  return code;
};


//SESSION CONSOLELOG
Blockly.Blocks['session_consolelog'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:consoleLog");
    this.appendDummyInput()
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField(new Blockly.FieldDropdown([["INFO", "info"], ["NOTICE", "notice"], ["ERR", "err"], ["DEBUG", "debug"], ["WARNING", "warning"]]), "Log Level");
    this.appendValueInput("msg")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("message");
    this.setInputsInline(false);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('Log something to the FreeSWITCH logger from session. Arguments are log level and message.');
  }
};


Blockly.Lua['session_consolelog'] = function(block) {
  var dropdown_log_level = block.getFieldValue('Log Level');
  var value_msg = Blockly.Lua.valueToCode(block, 'msg', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:consoleLog(\"' + dropdown_log_level + '\",' + value_msg + ');\n'
  return code;
};



//SESSION SPEAK
Blockly.Blocks['session_speak'] = {
  init: function() {
    this.appendValueInput("textstring")
        .setCheck("String")
        .appendField("session:speak");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('the TTS engine speaks the inputted textstring. Requeres that set_tts_params is called beforehand.');
  }
};

Blockly.Lua['session_speak'] = function(block) {
  var value_textstring = Blockly.Lua.valueToCode(block, 'textstring', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:speak(' + value_textstring + ');\n';
  return code;
};


//SET TTS_PARAMS
Blockly.Blocks['session_set_tts_params'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:set_tts_params");
    this.appendDummyInput()
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField(new Blockly.FieldDropdown([["Flite", "flite"]]), "engine");
    this.appendDummyInput()
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField(new Blockly.FieldDropdown([["slt (female)", "slt"], ["rms (male)", "rms"], ["kal (male)", "kal"]]), "voice");
    this.setInputsInline(false);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, "Boolean");
    this.setColour(65);
    this.setTooltip('Sets the TTS engine and voice to be used.');
  }
};


Blockly.Lua['session_set_tts_params'] = function(block) {
  var dropdown_engine = block.getFieldValue('engine');
  var dropdown_voice = block.getFieldValue('voice');
  var code = 'session:set_tts_params(\"' + dropdown_engine + '\", \"'+ dropdown_voice + '\");\n';
  return code;
};

// SESSION GETDIGITs

Blockly.Blocks['session_getdigits'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:getDigits");
    this.appendValueInput("max_digits")
        .setCheck("Number")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("max_digits");
    this.appendValueInput("terminator")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("terminator");
    this.appendValueInput("timeout")
        .setCheck("Number")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("timeout (seconds)");
    this.setInputsInline(false);
    this.setOutput(true, ["String", "Number"]);
    this.setColour(65);
    this.setTooltip('getDigits has three arguments: max_digits, terminators, timeout.');
  }
};

Blockly.Lua['session_getdigits'] = function(block) {
  var value_max_digits = Blockly.Lua.valueToCode(block, 'max_digits', Blockly.Lua.ORDER_ATOMIC);
  var value_terminator = Blockly.Lua.valueToCode(block, 'terminator', Blockly.Lua.ORDER_ATOMIC);
  var value_timeout = 1000 * Blockly.Lua.valueToCode(block, 'timeout', Blockly.Lua.ORDER_ATOMIC);
  if (value_terminator == ''){
    value_terminator = '#';
  }
  var code = 'session:getDigits(' + value_max_digits + ',\"' + value_terminator + '\",' + value_timeout + ');\n';
  // TODO: Change ORDER_NONE to the correct strength.
  return [code, Blockly.Lua.ORDER_FUNCTION_CALL];
};


//SESSION SET AUTO HANGUP
Blockly.Blocks['session_setautohangup'] = {
  init: function() {
    this.appendValueInput("condition")
        .setCheck("Boolean")
        .appendField("session:setAutoHangup()");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('http://www.example.com/');
  }
};

Blockly.Lua['session_setautohangup'] = function(block) {
  var value_condition = Blockly.Lua.valueToCode(block, 'condition', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:setAutoHangup(' + value_condition +');\n';
  return code;
};


//SESSION HANGUP
Blockly.Blocks['session_hangup'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:hangup()")
        .appendField(new Blockly.FieldDropdown([["Normal", "NORMAL_CLEARING"], ["User Busy", "USER_BUSY"], ["Call Rejected", "CALL_REJECTED"], ["No Answer", "NO_ANSWER"], ["Unspecified", "UNSPECIFIED"]]), "hangup_cause");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('http://www.example.com/');
  }
};


Blockly.Lua['session_hangup'] = function(block) {
  var dropdown_hangup_cause = block.getFieldValue('hangup_cause');
  var code = 'session:hangup(\''+ dropdown_hangup_cause +'\')\n';
  return code;
};


//SESSION BRIDGED
Blockly.Blocks['session_bridged'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:bridged()");
    this.setOutput(true, "Boolean");
    this.setColour(65);
    this.setTooltip("Check to see if this session's channel is bridged to another channel.");
  }
};


Blockly.Lua['session_bridged'] = function(block) {
  var code = 'session:bridged()';
  return [code, Blockly.Lua.ORDER_FUNCTION_CALL];
};


//SESSION GET VARIABLE
Blockly.Blocks['session_get_variable'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:getVariable()");
    this.setOutput(true, "Boolean");
    this.appendValueInput("variable_name")
        .setCheck("String")
        .appendField("Variable name");
    this.setColour(65);
    this.setTooltip("To get system variables such as ${hold_music}");
  }
};


Blockly.Lua['session_get_variable'] = function(block) {
  var value_variable_name = Blockly.Lua.valueToCode(block, 'variable_name', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:getVariable('+ value_variable_name +')';
  return [code, Blockly.Lua.ORDER_FUNCTION_CALL];
};


//SESSION SET VARIABLE
Blockly.Blocks['session_set_variable'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("session:setVariable()");
    this.setOutput(true, "Boolean");
    this.appendValueInput("variable_name")
        .setCheck("String")
        .appendField("Variable name");
    this.appendValueInput("variable_value")
        .setCheck("String")
        .appendField("Variable value");
    this.setColour(65);
    this.setTooltip("Set variable on a session");
  }
};


Blockly.Lua['session_set_variable'] = function(block) {
  var value_variable_name = Blockly.Lua.valueToCode(block, 'variable_name', Blockly.Lua.ORDER_ATOMIC);
  var value_value = Blockly.Lua.valueToCode(block, 'variable_value', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:setVariable('+ value_variable_name + ','+ value_value +')\n';
  return [code, Blockly.Lua.ORDER_FUNCTION_CALL];
};


