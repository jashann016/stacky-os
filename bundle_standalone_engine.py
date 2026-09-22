with open("/Users/jashanpreetsingh/Downloads/Stacky Ai /thinking_orbs_engine.js", "r") as f:
    code = f.read()

# Remove ES module export syntax at the bottom
lines = code.splitlines()
clean_lines = []
for line in lines:
    if line.strip().startswith("export {"):
        # convert export { resolvePreset, MODE_DRAWS } to window variables
        clean_lines.append("window.ThinkingEngine = { resolvePreset, MODE_DRAWS };")
    else:
        clean_lines.append(line)

new_code = "\n".join(clean_lines)
with open("/Users/jashanpreetsingh/Downloads/Stacky Ai /thinking_engine_standalone.js", "w") as f:
    f.write(new_code)

print("Created standalone thinking_engine_standalone.js with window.ThinkingEngine global!")
