Blockly.Blocks['start_call'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Answer Call");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('');
  }
};


Blockly.Lua['start_call'] = function(block) {
  var code = '';
  code += `
function onInput (s, type, obj)
    if ( type == 'dtmf' ) then
        return "break" -- This ends the recording
    end
end
session:setInputCallback("onInput","")
`;
  code += 'session:answer();\n';
  code += 'session:set_tts_params("flite", "slt");\n';
  return code;
};


Blockly.Blocks['end_call'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("End Call");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('');
  }
};


Blockly.Lua['end_call'] = function(block) {
  var code = 'session:hangup();\n';
  return code;
};


//SESSION SPEAK
Blockly.Blocks['speak_text'] = {
  init: function() {
    this.appendValueInput("textstring")
        .setCheck("String")
        .appendField("Speak Text");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('the TTS engine speaks the inputted textstring. Requeres that set_tts_params is called beforehand.');
  }
};

Blockly.Lua['speak_text'] = function(block) {
  var value_textstring = Blockly.Lua.valueToCode(block, 'textstring', Blockly.Lua.ORDER_ATOMIC);
  var code = 'session:speak(' + value_textstring + ');\n';
  var code = code + 'session:sleep(100);\n'
  return code;
};


Blockly.Blocks['play_music'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Play music")
        .appendField(new Blockly.FieldDropdown([["Bong sound", "tone_stream://v=-7;%(100,0,941.0,1477.0);v=-7;>=2;+=.1;%(1000, 0, 640)"], ["Danza Espanola", "/usr/share/freeswitch/sounds/music/default/8000/danza-espanola-op-37-h-142-xii-arabesca.wav"], ["Partita #3", "/usr/share/freeswitch/sounds/music/default/8000/partita-no-3-in-e-major-bwv-1006-1-preludio.wav"], ["Preludio", "/usr/share/freeswitch/sounds/music/default/8000/ponce-preludio-in-e-major.wav"], ["Suite Espanola", "/usr/share/freeswitch/sounds/music/default/8000/suite-espanola-op-47-leyenda.wav"]]), "musicfiles");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('Plays the file endless to the session. Pressing any key will stop playing the music.');
    this.setHelpUrl('http://www.example.com/');
  }
};

Blockly.Lua['play_music'] = function(block) {
  var dropdown_musicfiles = block.getFieldValue('musicfiles');
  var code = 'session:streamFile(\'' + dropdown_musicfiles +'\');\n';
  return code;
};


Blockly.Blocks['record_file'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Make a Recording");
    this.appendValueInput("welcome_msg")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("Welcome Message");
    this.appendValueInput("filename")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("Filename");
    this.appendValueInput("max_len_secs")
        .setCheck("Number")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("Max length of recording (seconds)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('');
    this.setHelpUrl('http://www.example.com/');
  }
};

Blockly.Lua['record_file'] = function(block) {
  var value_welcome_msg = Blockly.Lua.valueToCode(block, 'welcome_msg', Blockly.Lua.ORDER_ATOMIC);
  var value_filename = Blockly.Lua.valueToCode(block, 'filename', Blockly.Lua.ORDER_ATOMIC);
  var value_max_len_secs = Blockly.Lua.valueToCode(block, 'max_len_secs', Blockly.Lua.ORDER_ATOMIC);

  var code = '';
  code += 'session:speak('+ value_welcome_msg +');\n';
  code += 'session:sleep(100);\n';
  code += 'session:recordFile(' + value_filename +', ' + value_max_len_secs +', 10, 3);\n';
  return code;
};


Blockly.Blocks['record_file_2'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Audio Recording with user verification");
    this.appendValueInput("directory")
        .setCheck("String")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("Directory");
    this.appendValueInput("max_len_secs")
        .setCheck("Number")
        .setAlign(Blockly.ALIGN_RIGHT)
        .appendField("Max length of recording (seconds)");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('');
    this.setHelpUrl('http://www.example.com/');
  }
};

Blockly.Lua['record_file_2'] = function(block) {
  var value_directory = Blockly.Lua.valueToCode(block, 'directory', Blockly.Lua.ORDER_ATOMIC);
  var value_max_len_secs = Blockly.Lua.valueToCode(block, 'max_len_secs', Blockly.Lua.ORDER_ATOMIC);

  var code = '';
  code += 'dir = ' + value_directory + '\n';
  code += 'max_len_secs = ' + value_max_len_secs + '\n';
  code += `
-- Voice Recording Block
msgnum = os.time()
session:sleep(100)
-- New loop: accepted or not
accepted = false

while (session:ready() and not accepted) do
    -- Record ile
    session:streamFile("phrase:voicemail_record_message")
    -- Play a "bong" tone prior to recording
    session:streamFile("tone_stream://v=-7;%(100,0,941.0,1477.0);v=-7;>=2;+=.1;%(1000, 0, 640)")
    filename = dir.."/"..msgnum..".wav"
    session:recordFile(filename,max_len_secs,100,10)
    -- New loop: Ask caller to listen, accept, or re-record
    listen = true
    while ( session:ready() and listen ) do
        session:streamFile(filename)
        -- Use handy record_file_check macro courtesy of the voicemail module
        local digits = session:playAndGetDigits(1, 1, 2, 4000, "#", "phrase:voicemail_record_file_check:1:2:3", "ivr/ivr-that_was_an_invalid_entry.wav", "\\\\d{1}")
        if (digits == "1") then
            listen = true
            accepted = false
            session:execute("sleep","500")
        elseif (digits == "2") then
            listen = false
            accepted = true
            -- Let the caller know that the message is saved
            -- NOTE: you could put these into a Phrase Macro as well
            session:streamFile("voicemail/vm-message.wav")
            session:execute("sleep","100")
            session:execute("say","en number iterated " .. msgnum)
            session:execute("sleep","100")
            session:streamFile("voicemail/vm-saved.wav")
            session:execute("sleep","1500")
         elseif ( digits =="3" ) then
            listen = false
            accepted = false
            session:execute("sleep","500")
        end -- if ( digits == "1" )
    end -- while ( listen )
end -- while ( not accepted )
  `;

  return code;
};
