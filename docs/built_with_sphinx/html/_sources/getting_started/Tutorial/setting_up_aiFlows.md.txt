# Setting up aiFlows
Welcome to a straightforward tutorial in which we walk you through a suggested setup that will provide you with a smooth and efficient workflow.


Let's dive right in. This document is a tutorial for setting up the following:

1. [Section 1:](#section-1-installing-aiflows) Installing aiFlows
2. [Section 2:](#section-2-setting-up-the-flowverse) Setting Up The FlowVerse
3. [Section 3:](#section-3-setting-up-your-api-keys) Setting Up Your API Keys


### By the Tutorial's End, I Will Have...
* Installed the aiFlows library successfully
* Established an organized file structure for seamless collaboration within the FlowVerse
* Set up a Hugging Face account for contribution to the FlowVerse (Optional)
* Configured and activated my API keys

## Section 1: Installing aiFlows
Begin the installation process for aiFlows with Python 3.10+ using:
```basha
pip install aiflows
```
Alternatively, for a manual installation:

```bash
git clone https://github.com/epfl-dlab/aiflows.git
cd aiflows
conda create --name flows python=3.10
conda activate flows
pip install -e .
```

## Section 2: Setting Up The FlowVerse

### Step 1: Setting up efficient Folder Structure
Create a dedicated folder for the FlowVerse, following our recommended structure:
```bash
mkdir FlowVerse
```
Following the download of your initial Flows from the FlowVerse, your folder arrangement should look like this:
```bash
|-- YourProject
|-- flow_modules
|      |-- Flow1
|      |-- Flow2
|      |-- ...
```
This ensures all your Flows are conveniently centralized in a single place, simplifying management.

### Step 2: Optional - Linking Hugging Face for FlowVerse Push

To facilitate FlowVerse pushing, it's essential to link your Hugging Face account:
1. Begin by creating a [Hugging Face](https://huggingface.co/join) account at huggingface and verify your email.
2. Log in to Hugging Face in the terminal using:
    * For terminal login, you'll need an access token. If you haven't already, [created one](https://huggingface.co/settings/tokens) (a read token should be sufficient)
    * Enter the following command in the terminal, and when prompted, paste your access token:
        ```
        huggingface-cli login
        ```

This process is essential for the smooth integration of Hugging Face with FlowVerse, ensuring effortless pushing.

## Section 3: Setting Up Your API Keys

In this final step, let's configure your API keys as environment variables for your conda environment. We'll demonstrate how to set up keys for both OpenAI and Azure. Note that, thanks to LiteLLM, a variety of providers are available—explore them here: https://docs.litellm.ai/docs/providers

* If you're using openAI:
    * write in your terminal:
        ```
        conda env config vars set OPENAI_API_KEY=<YOUR-OPEN-AI-API_KEY>
        ```
    * reactivate your conda environment:
        ```
        conda activate <NAME_OF_YOUR_ENVIRONMENT>
        ```
    * To make sure that your key has been set as an environment variable (your environment variables should appear):
        ```
        conda env config vars list
        ```
* If you're using Azure:
    * write in your terminal:
        ```
        conda env config vars set AZURE_OPENAI_KEY=<YOUR-AZURE_OPENAI_KEY>
        conda env config vars set AZURE_API_BASE=<YOUR-AZURE_API_BASE>
        conda env config vars set AZURE_API_VERSION=<YOUR-AZURE_API_VERSION>
        ```
    * reactivate your conda environment:
        ```
        conda activate <NAME_OF_YOUR_ENVIRONMENT>
        ```
    * To make sure that your key has been set as an environment variable (your environment variables should appear):
        ```
        conda env config vars list
        ```

Congratulations! You are now equipped to seamlessly work with aiFlows. Happy flowing!
