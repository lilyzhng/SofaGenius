# TODO
-[x] 1. analyze the dataset lilyzhng/uigen-ui-code-gen-full

-[x] 2. Flow format: I'll analyze the dataset lilyzhng/uigen-ui-code-gen-full for you.                                                                          
  ⎿  Let me start by discovering its schema to understand what data it contains
    ⎿  I can see this is a UI code generation dataset focused on HTML/CSS with Tailwind CSS.
  ⎿ Let me run a comprehensive analysis to understand the dataset better.

-[x] 3. alphabetically, should be 0-5k, 5k-10k, 10k-15k, 15k-20k, 20k+,  intsead of the current 0-5k, 10k-15k, 15k-20k, 20k+, 5k-10k 

-[] 4. When I say "Show me examples of specific UI components (e.g., landing pages, dashboards)", it should be able to render the sample script 

-[] 5.If phrase  3 is already completed, I think we should consider phrase number 4. Also, before doing that, we  
  should refactor the code for sub-agents so that it wouldn't be too many tool calls and make it too confusing. I
  don't know. I wonder if phrase number 4 is about launch training/eval using modal. I think that would be the      
  most aha moment. refer to @STATE.md for phrase 4 info. Then draft a comprehensive plan for Phase 4.    

-[] 6. Here comes the issue. When the job first gets created, it shows this card which is showing            
  company running, and the project link is linked to its generic project link:                          
  https://wandb.ai/alchemxz/qwen-coder-code-gen, When a user clicks on this link, they would be         
  clueless about what to check because there are many runs under this project. I believe this is a      
  risk condition. When we first created the card, we don't have the information about the wannabe       
  link yet. That's why I put the project link. Later on, when I ask what is the current status of       
  the project, in the chat interface it actually gives me the correct link of the specific run          
  https://wandb.ai/alchemxz/qwen-coder-code-gen/runs/e8itsvrm                                           
                                                                                                        
  How do we want to fix this issue? I think maybe after launching the job from the chat, the agent      
  would try to wait for some time and try to get the wandb link for the specific run properly. this     
   would be one of the function calls or two calls, and then on the right we update the link            
  properly so that we don't put the wrong link.                                                         
  ⎿  [Image #10]  

-[] 7.for this project, write a SofaGenius.md file, explains the whole project in plain language. 

Explain the technical architecture, the structure of the codebase and how the various parts are connected, the technologies used, why we made these technical decisions, and lessons I can learn from it (this should include the bugs we ran into and how we fixed them, potential pitfalls and how to avoid them in the future, new technologies used, how good engineers think and work, best practices, etc). 

It should be very engaging to read; don't make it sound like boring technical documentation/textbook. Where appropriate, use analogies and anecdotes to make it more understandable and memorable.

Also think from the Product perspective: what are the aha moments? Why would the user find this tool super useful? Did we democratize, you know, everyone to be a researcher? 

- 8. The other feature I love is on-the-fly dynamic config. I can simply say, "Change it to use 20 epochs instead of 10. Change to use 10,000 frames instead of 5,000." The agent understands how to modify the config, and we can launch a new job without any friction. Traditionally, we have to keep our eyes very big and play with the parameter. Hopefully there is no human error, but always we make some stupid mistake, and then we have to relaunch the training. By doing this kind of modification while talking with the agent, it really makes the mode of training and research much easier to handle!

- 9. The other feature is when you do independent research, you only be careful about your bank. You don't want to break your bank while doing different jobs. By talking with the agent, you can do clear budget control and understand how much it's going to cost before committing.

- 10. Another thing is that Wannabe can be overwhelming if you have over 10,000 experiments launched throughout the year. Sometimes it's just hard to find and manually manage those training runs from one to another and try to overlay them on top of each other. Right now, this chatting interface makes everything so much easier. All you need to do is know the Wannabe around name, or you can just say, "Hey, compare these jobs with my previous jobs, overlay them on top of each other, and show me what's the difference." This just makes the entire Wannabe visualization inspection much easier.

- [] We need to figure out a way to document the trace, basically the interaction between the agent and the user. If the user gives us some style, it means that the agent must have done something wrong. Then we need to fix it. On top of that, I think it would be helpful to use this trace data, the long trajectory data, to train an ML agent that understands the context very well.Gradually, we will use this agent to do scouting, research, and everything. Your agent can also be developed with your own research tastes. That can be tailored and fine-tuned reinforcement learning to assist you much better.