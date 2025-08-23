🚀 How to Copy Files to Your DigitalOcean Server with SCP
🛠️ Prerequisites
✅ You have SSH access to your server (root@206.189.30.236)
✅ Your SSH key is set up and working
1️⃣ Prepare Your SSH Key

# Copy your private key to the SSH directorycp /home/angel/helix-hub/DO_Keys ~/.ssh/id_ed25519chmod 600 ~/.ssh/id_ed25519# Copy your public key (for reference)cp /home/angel/helix-hub/DO_Keys.pub ~/.ssh/id_ed25519.pub
🔑 Your key is now ready!

2️⃣ Add Your Public Key to the Server

ssh-copy-id -i ~/.ssh/id_ed25519.pub root@206.189.30.236
🔓 This step allows passwordless login!

3️⃣ Test SSH Login

ssh root@206.189.30.236
🟢 If you see the server shell, you’re good to go!

4️⃣ Copy Your File with SCP

scp /home/angel/helix-hub/README.md root@206.189.30.236:/root/helix-hub/README.md
📤 This command securely transfers your file!

5️⃣ (Optional) Copy a Whole Folder

scp -r /home/angel/helix-hub root@206.189.30.236:/root/
📁 Use -r for recursive folder copy!

🏁 Summary
🔑 Set up your SSH key
🔓 Add your public key to the server
🟢 Test SSH login
📤 Use SCP to copy files or folders
Now you can transfer files to your server like a pro! 🐣🚀
