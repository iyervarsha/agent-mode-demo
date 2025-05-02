document.addEventListener('DOMContentLoaded', () => {
    // Get all form elements we'll interact with
    const featureForm = document.getElementById('feature-form');
    const specForm = document.getElementById('spec-form');
    const screenshotForm = document.getElementById('screenshot-form');
    const formInputBtn = document.getElementById('form-input-btn');
    const specInputBtn = document.getElementById('spec-input-btn');
    const screenshotInputBtn = document.getElementById('screenshot-input-btn');
    const featureCategory = document.getElementById('feature-category');
    const featureCategorySpec = document.getElementById('feature-category-spec');
    const featureCategoryScreenshot = document.getElementById('feature-category-screenshot');
    const newCategoryGroup = document.getElementById('new-category-group');
    const newCategoryGroupSpec = document.getElementById('new-category-group-spec');
    const newCategoryGroupScreenshot = document.getElementById('new-category-group-screenshot');
    const generateBtn = document.getElementById('generate-btn');
    const generateBtnSpec = document.getElementById('generate-btn-spec');
    const generateBtnScreenshot = document.getElementById('generate-btn-screenshot');
    const outputSection = document.getElementById('output-section');
    const previewContainer = document.getElementById('preview-container');
    const markdownOutput = document.getElementById('markdown-output');
    const copyRawBtn = document.getElementById('copy-raw-btn');
    const copyArticleBtn = document.getElementById('copy-article-btn');
    const downloadMdBtn = document.getElementById('download-md-btn');
    const backBtn = document.getElementById('back-btn');
    const screenshotUpload = document.getElementById('screenshot-upload');
    const screenshotPreview = document.getElementById('screenshot-preview');
    const screenshotDropzone = document.getElementById('screenshot-dropzone');
    const screenshotControls = document.getElementById('screenshot-controls');
    const screenshotCountElem = document.getElementById('screenshot-count');
    const clearScreenshotsBtn = document.getElementById('clear-screenshots');

    // Toggle between input methods
    formInputBtn.addEventListener('click', function() {
        featureForm.style.display = 'block';
        specForm.style.display = 'none';
        screenshotForm.style.display = 'none';
        formInputBtn.classList.add('active');
        specInputBtn.classList.remove('active');
        screenshotInputBtn.classList.remove('active');
    });

    specInputBtn.addEventListener('click', function() {
        featureForm.style.display = 'none';
        specForm.style.display = 'block';
        screenshotForm.style.display = 'none';
        formInputBtn.classList.remove('active');
        specInputBtn.classList.add('active');
        screenshotInputBtn.classList.remove('active');
    });

    screenshotInputBtn.addEventListener('click', function() {
        featureForm.style.display = 'none';
        specForm.style.display = 'none';
        screenshotForm.style.display = 'block';
        formInputBtn.classList.remove('active');
        specInputBtn.classList.remove('active');
        screenshotInputBtn.classList.add('active');
    });

    // Show new category input if "Create New Category" option is selected
    featureCategory.addEventListener('change', function() {
        if (this.value === 'new-category') {
            newCategoryGroup.style.display = 'block';
        } else {
            newCategoryGroup.style.display = 'none';
        }
    });

    // Show new category input for spec form if "Create New Category" option is selected
    featureCategorySpec.addEventListener('change', function() {
        if (this.value === 'new-category') {
            newCategoryGroupSpec.style.display = 'block';
        } else {
            newCategoryGroupSpec.style.display = 'none';
        }
    });

    // Show new category input for screenshot form if "Create New Category" option is selected
    featureCategoryScreenshot.addEventListener('change', function() {
        if (this.value === 'new-category') {
            newCategoryGroupScreenshot.style.display = 'block';
        } else {
            newCategoryGroupScreenshot.style.display = 'none';
        }
    });

    // Configure server settings
    const serverConfig = {
        useLocalServer: true, // Set to true to use our Python Flask backend
        serverUrl: 'http://localhost:5000' // The URL of our Flask server
    };

    // Replace the OpenAI API configuration and form elements with Azure backend info
    const createAIEnhanceGroup = (id, statusId) => {
        const group = document.createElement('div');
        group.className = 'form-group ai-enhance-group';
        group.innerHTML = `
            <label for="${id}">AI Enhancement Options:</label>
            <div class="checkbox-group">
                <input type="checkbox" id="${id}" name="${id}" checked>
                <label for="${id}">Use Azure OpenAI to enhance documentation</label>
            </div>
            <div id="${statusId}">
                <p><small>Note: Browser authentication will be used when you first generate documentation</small></p>
            </div>
            <select id="${id}-type" name="${id}-type">
                <option value="refine">Refine and polish content</option>
                <option value="expand">Expand with additional details</option>
                <option value="technical">Make more technical</option>
                <option value="simplify">Simplify for broader audience</option>
                <option value="match-style">Match Microsoft documentation style</option>
            </select>
        `;
        return group;
    };

    // Create AI enhancement groups for each form
    const aiEnhanceGroup = createAIEnhanceGroup('ai-enhance', 'azure-auth-status');
    const aiEnhanceGroupSpec = createAIEnhanceGroup('ai-enhance-spec', 'azure-auth-status-spec');
    const aiEnhanceGroupScreenshot = createAIEnhanceGroup('ai-enhance-screenshot', 'azure-auth-status-screenshot');
    
    // Get button groups
    const generateBtnGroup = document.querySelector('#generate-btn').closest('.form-group');
    const generateBtnGroupSpec = document.querySelector('#generate-btn-spec').closest('.form-group');
    const generateBtnGroupScreenshot = document.querySelector('#generate-btn-screenshot').closest('.form-group');
    
    // Remove old API key elements if they exist
    const oldApiKeyGroup = document.getElementById('api-key') ? 
        document.getElementById('api-key').closest('.form-group') : null;
    if (oldApiKeyGroup) {
        oldApiKeyGroup.remove();
    }
    
    // Remove old AI enhance groups if they exist
    document.querySelectorAll('.ai-enhance-group').forEach(group => group.remove());
    
    // Add the AI enhance groups to forms
    featureForm.insertBefore(aiEnhanceGroup, generateBtnGroup);
    specForm.insertBefore(aiEnhanceGroupSpec, generateBtnGroupSpec);
    screenshotForm.insertBefore(aiEnhanceGroupScreenshot, generateBtnGroupScreenshot);

    // Add loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '<div class="spinner"></div><p>Generating enhanced documentation using Azure OpenAI...</p>';
    loadingIndicator.style.display = 'none';
    document.querySelector('.container').appendChild(loadingIndicator);

    // Handle screenshot uploads and previews
    const uploadedScreenshots = [];

    // Function to update screenshot count display
    function updateScreenshotCount() {
        const count = uploadedScreenshots.length;
        screenshotCountElem.textContent = count === 1 
            ? '1 screenshot uploaded'
            : `${count} screenshots uploaded`;
        
        // Show/hide screenshot controls
        screenshotControls.style.display = count > 0 ? 'flex' : 'none';
    }

    // Clear all screenshots button
    clearScreenshotsBtn.addEventListener('click', function() {
        // Clear all screenshots
        uploadedScreenshots.length = 0;
        screenshotPreview.innerHTML = '';
        updateScreenshotCount();
    });
    
    // Handle file selection through input
    screenshotUpload.addEventListener('change', function() {
        handleFileUpload(this.files);
    });
    
    // Handle drag and drop events
    screenshotDropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
    });
    
    screenshotDropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
    });
    
    screenshotDropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files);
        }
    });
    
    // Handle click on dropzone
    screenshotDropzone.addEventListener('click', function(e) {
        // Don't trigger if clicking on the button
        if (!e.target.classList.contains('file-select-btn')) {
            screenshotUpload.click();
        }
    });
    
    // Process uploaded files
    function handleFileUpload(files) {
        if (files.length === 0) return;
        
        // Process each file
        Array.from(files).forEach(file => {
            // Check if file is an image
            if (!file.type.match('image.*')) {
                return;
            }
            
            // Check for duplicate files
            if (uploadedScreenshots.some(s => s.name === file.name && s.size === file.size)) {
                console.log('Skipping duplicate file:', file.name);
                return;
            }

            // Store file data
            uploadedScreenshots.push({
                file: file,
                name: file.name,
                size: file.size
            });

            // Create preview element
            const previewItem = document.createElement('div');
            previewItem.className = 'screenshot-preview-item';
            
            // Create image preview
            const img = document.createElement('img');
            const reader = new FileReader();
            reader.onload = function(e) {
                img.src = e.target.result;
            }
            reader.readAsDataURL(file);
            
            // Create remove button
            const removeBtn = document.createElement('button');
            removeBtn.className = 'screenshot-preview-remove';
            removeBtn.innerHTML = '×';
            removeBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent triggering dropzone click
                
                // Remove from array
                const index = uploadedScreenshots.findIndex(s => s.name === file.name);
                if (index > -1) {
                    uploadedScreenshots.splice(index, 1);
                }
                // Remove from preview
                previewItem.remove();
                // Update count
                updateScreenshotCount();
            });
            
            // Add elements to preview
            previewItem.appendChild(img);
            previewItem.appendChild(removeBtn);
            screenshotPreview.appendChild(previewItem);
            
            // Update count
            updateScreenshotCount();
        });
    }

    // Handle the documentation generation from form input
    generateBtn.addEventListener('click', async () => {
        if (!validateForm(featureForm)) return;

        // Get all form values
        const featureName = document.getElementById('feature-name').value;
        let category = featureCategory.value;
        if (category === 'new-category') {
            category = document.getElementById('new-category-name').value;
        }
        const docType = document.getElementById('documentation-type').value;
        const featureDesc = document.getElementById('feature-description').value;
        const prerequisites = document.getElementById('prerequisites').value;
        const configSteps = document.getElementById('configuration-steps').value;
        const screenshots = document.getElementById('screenshots').value;
        const bestPractices = document.getElementById('best-practices').value;
        const limitations = document.getElementById('limitations').value;
        
        // Check if AI enhancement is enabled
        const useAI = document.getElementById('ai-enhance').checked;
        const enhancementType = document.getElementById('ai-enhance-type').value;

        // Generate basic markdown documentation
        let markdown = generateMarkdown(
            featureName, 
            category,
            docType,
            featureDesc, 
            prerequisites, 
            configSteps, 
            screenshots, 
            bestPractices, 
            limitations
        );

        // Apply Azure OpenAI enhancement if enabled
        if (useAI && serverConfig.useLocalServer) {
            markdown = await enhanceWithAzure(
                markdown,
                featureName,
                category,
                docType,
                enhancementType,
                'azure-auth-status',
                loadingIndicator
            );
        }

        // Display the markdown
        displayMarkdown(markdown);
    });

    // Handle the documentation generation from spec input
    generateBtnSpec.addEventListener('click', async () => {
        if (!validateForm(specForm)) return;

        // Get all form values
        const featureName = document.getElementById('feature-name-spec').value;
        let category = featureCategorySpec.value;
        if (category === 'new-category') {
            category = document.getElementById('new-category-name-spec').value;
        }
        const docType = document.getElementById('documentation-type-spec').value;
        const specText = document.getElementById('spec-text').value;
        
        // Check if AI enhancement is enabled
        const useAI = document.getElementById('ai-enhance-spec').checked;
        const enhancementType = document.getElementById('ai-enhance-type-spec').value;

        // Generate initial markdown from the spec text
        let markdown = generateMarkdownFromSpec(
            featureName,
            category,
            docType,
            specText
        );

        // Apply Azure OpenAI enhancement if enabled
        if (useAI && serverConfig.useLocalServer) {
            markdown = await enhanceWithAzure(
                markdown,
                featureName,
                category,
                docType,
                enhancementType,
                'azure-auth-status-spec',
                loadingIndicator
            );
        }

        // Display the markdown
        displayMarkdown(markdown);
    });

    // Handle the documentation generation from screenshots
    generateBtnScreenshot.addEventListener('click', async () => {
        try {
            console.log("Screenshot button clicked");
            
            // Basic validation
            if (!validateForm(screenshotForm)) {
                console.log("Form validation failed");
                return;
            } 
            
            if (uploadedScreenshots.length === 0) {
                console.log("No screenshots uploaded");
                alert('Please upload at least one screenshot.');
                return;
            }

            console.log("Form validation passed, proceeding with screenshot analysis");

            // Get form values
            const featureName = document.getElementById('feature-name-screenshot').value;
            let category = featureCategoryScreenshot.value;
            if (category === 'new-category') {
                category = document.getElementById('new-category-name-screenshot').value;
            }
            const docType = document.getElementById('documentation-type-screenshot').value;
            const additionalContext = document.getElementById('screenshot-description').value;
            
            console.log("Form values:", {
                featureName,
                category,
                docType,
                additionalContext,
                screenshotCount: uploadedScreenshots.length
            });
            
            // Check if AI enhancement is enabled
            const useAIElement = document.getElementById('ai-enhance-screenshot');
            if (!useAIElement) {
                console.error("Could not find AI enhancement checkbox element");
            }
            const useAI = useAIElement ? useAIElement.checked : false;
            
            const enhTypeElement = document.getElementById('ai-enhance-type-screenshot');
            if (!enhTypeElement) {
                console.error("Could not find enhancement type select element");
            }
            const enhancementType = enhTypeElement ? enhTypeElement.value : 'refine';
            
            console.log("AI settings:", {
                useAI,
                enhancementType
            });

            // Check server config
            console.log("Server config:", serverConfig);
            if (!serverConfig.serverUrl) {
                alert('Server URL is not configured. Please check the server settings.');
                return;
            }

            // Show loading indicator
            loadingIndicator.style.display = 'flex';
            loadingIndicator.querySelector('p').textContent = 'Processing screenshots and generating documentation...';
            
            // Inform user about Azure authentication
            const statusElement = document.getElementById('azure-auth-status-screenshot');
            if (statusElement) {
                statusElement.innerHTML = 
                    '<p><small>Processing screenshots... A browser window may open for Azure authentication</small></p>';
            }
            
            console.log("Converting screenshots to base64...");
            // Convert screenshots to base64
            const screenshotData = await Promise.all(
                uploadedScreenshots.map(async (screenshot) => {
                    try {
                        const base64 = await fileToBase64(screenshot.file);
                        return {
                            name: screenshot.name,
                            base64: base64
                        };
                    } catch (error) {
                        console.error(`Error converting screenshot ${screenshot.name} to base64:`, error);
                        throw new Error(`Failed to process screenshot ${screenshot.name}: ${error.message}`);
                    }
                })
            );
            
            console.log("Screenshots converted successfully. Sending to server...", {
                screenshotsCount: screenshotData.length,
                names: screenshotData.map(s => s.name)
            });
            
            // Send to server for analysis
            console.log(`Sending request to ${serverConfig.serverUrl}/api/analyze-screenshots`);
            const response = await fetch(`${serverConfig.serverUrl}/api/analyze-screenshots`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    featureName,
                    category,
                    docType,
                    enhancementType,
                    additionalContext,
                    screenshots: screenshotData
                })
            });
            
            console.log("Server response status:", response.status);
            
            if (!response.ok) {
                let errorMessage = `Server responded with status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    console.error("Failed to parse error response:", e);
                }
                throw new Error(errorMessage);
            }
            
            console.log("Server response is OK, parsing JSON...");
            const result = await response.json();
            console.log("Received response from server");
            
            let markdown = result.markdown;
            
            // Apply additional enhancement if enabled
            if (useAI && serverConfig.useLocalServer) {
                console.log("Applying additional AI enhancement...");
                if (statusElement) {
                    statusElement.innerHTML = 
                        '<p><small>Enhancing documentation with Azure OpenAI...</small></p>';
                }
                
                markdown = await enhanceWithAzureOpenAI(
                    markdown,
                    featureName,
                    category,
                    docType,
                    enhancementType
                );
                
                console.log("AI enhancement complete");
            }
            
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Update authentication status
            if (statusElement) {
                statusElement.innerHTML = 
                    '<p><small>✓ Processing completed successfully</small></p>';
            }
                
            // Display the markdown
            console.log("Displaying generated documentation");
            displayMarkdown(markdown);
            
        } catch (error) {
            console.error('Screenshot analysis error:', error);
            alert('Error analyzing screenshots: ' + error.message);
            loadingIndicator.style.display = 'none';
            
            // Update status
            const statusElement = document.getElementById('azure-auth-status-screenshot');
            if (statusElement) {
                statusElement.innerHTML = 
                    `<p><small>⚠️ Screenshot analysis failed: ${error.message}. See console for details.</small></p>`;
            }
        }
    });

    // Helper function to convert file to base64
    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                // Remove the data URL prefix (data:image/jpeg;base64,)
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = error => reject(error);
        });
    }

    // Form validation helper
    function validateForm(form) {
        const requiredInputs = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
            } else {
                input.classList.remove('error');
            }
        });

        if (!isValid) {
            alert('Please fill out all required fields.');
        }
        
        return isValid;
    }

    // Helper function to enhance with Azure OpenAI
    async function enhanceWithAzure(markdown, featureName, category, docType, enhancementType, statusElementId, loadingIndicator) {
        try {
            // Show loading indicator
            loadingIndicator.style.display = 'flex';
            
            // Inform the user that browser authentication may be needed
            document.getElementById(statusElementId).innerHTML = 
                '<p><small>Azure authentication in progress... A browser window may open for login</small></p>';
            
            // Get AI-enhanced documentation from our Python backend
            const enhancedMarkdown = await enhanceWithAzureOpenAI(
                markdown,
                featureName,
                category,
                docType,
                enhancementType
            );
            
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Update authentication status
            document.getElementById(statusElementId).innerHTML = 
                '<p><small>✓ Azure authentication successful</small></p>';
                
            return enhancedMarkdown;
        } catch (error) {
            console.error('AI enhancement error:', error);
            alert('Error enhancing documentation with Azure OpenAI: ' + error.message);
            loadingIndicator.style.display = 'none';
            
            // Update authentication status
            document.getElementById(statusElementId).innerHTML = 
                '<p><small>⚠️ Azure authentication failed. See console for details.</small></p>';
                
            return markdown; // Return original markdown if enhancement fails
        }
    }

    // Function to display markdown output
    function displayMarkdown(markdown) {
        // Convert markdown to HTML with enhanced formatting for article-like appearance
        const htmlArticle = convertMarkdownToArticle(markdown);
        
        // Display the formatted article in the preview container
        previewContainer.innerHTML = htmlArticle;
        
        // Store the raw markdown for download/copy functionality
        markdownOutput.textContent = markdown;
        
        // Hide the raw markdown display
        document.querySelector('.output-markdown').style.display = 'none';
        
        // Make the preview container take full width
        document.querySelector('.output-preview').style.width = '100%';
        document.querySelector('.output-preview h3').textContent = 'Article Preview:';
        
        // Show output section, hide input forms
        document.querySelector('.input-section').style.display = 'none';
        outputSection.style.display = 'block';
    }
    
    /**
     * Convert markdown to a well-formatted HTML article
     * with cleaner formatting and no markdown artifacts
     */
    function convertMarkdownToArticle(markdown) {
        if (!markdown) return '';
        
        let html = markdown;
        
        // First, handle code blocks to avoid processing their contents
        const codeBlocks = [];
        html = html.replace(/```([a-z]*)\n([\s\S]*?)\n```/g, function(match) {
            codeBlocks.push(match);
            return `CODE_BLOCK_${codeBlocks.length - 1}`;
        });
        
        // Handle inline code before other formatting
        const inlineCodes = [];
        html = html.replace(/`([^`]+)`/g, function(match) {
            inlineCodes.push(match);
            return `INLINE_CODE_${inlineCodes.length - 1}`;
        });
        
        // Headers with proper styling
        html = html.replace(/^# (.*$)/gm, '<h1 class="article-title">$1</h1>');
        html = html.replace(/^## (.*$)/gm, '<h2 class="article-section">$1</h2>');
        html = html.replace(/^### (.*$)/gm, '<h3 class="article-subsection">$1</h3>');
        
        // Fix bullets with dashes - remove the dash after the bullet
        html = html.replace(/• - /g, '• ');
        
        // Clean up numbered lists
        html = html.replace(/^(\d+\.\d+\.)\s*\*\*(.*?)\*\*/gm, '<li class="article-list-item"><strong>$1 $2</strong></li>');
        html = html.replace(/^(\d+\.)\s*\*\*(.*?)\*\*/gm, '<li class="article-list-item"><strong>$1 $2</strong></li>');
        html = html.replace(/^(\d+\.\d+\.)\s*(.*?)$/gm, '<li class="article-list-item">$1 $2</li>');
        html = html.replace(/^(\d+\.)\s*(.*?)$/gm, '<li class="article-list-item">$1 $2</li>');
        
        // Clean up bullet lists - handle various formats
        html = html.replace(/^• - (.*?)$/gm, '<li class="article-list-item">$1</li>');
        html = html.replace(/^• (.*?)$/gm, '<li class="article-list-item">$1</li>');
        html = html.replace(/^\* (.*?)$/gm, '<li class="article-list-item">$1</li>');
        html = html.replace(/^- (.*?)$/gm, '<li class="article-list-item">$1</li>');
        
        // Wrap lists with ul/ol elements
        html = html.replace(/(<li class="article-list-item">\d+\.\d+\..*?<\/li>(\n|$))+/g, '<ol class="article-list article-nested-list">$&</ol>');
        html = html.replace(/(<li class="article-list-item">\d+\..*?<\/li>(\n|$))+/g, '<ol class="article-list">$&</ol>');
        html = html.replace(/(<li class="article-list-item">.*?<\/li>(\n|$))+/g, '<ul class="article-list">$&</ul>');
        
        // Bold text (handle double asterisks)
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic text (handle single asterisks)
        html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
        
        // Format notes/callouts with nicer styling
        html = html.replace(/> \[!NOTE\]\n> (.*)/g, 
            '<div class="article-note"><span class="note-title">NOTE</span><p>$1</p></div>');
        html = html.replace(/> \[!WARNING\]\n> (.*)/g, 
            '<div class="article-warning"><span class="warning-title">WARNING</span><p>$1</p></div>');
        html = html.replace(/> \[!TIP\]\n> (.*)/g, 
            '<div class="article-tip"><span class="tip-title">TIP</span><p>$1</p></div>');
        
        // Process links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="article-link">$1</a>');
        
        // Paragraphs (after other formatting)
        // First, identify text that hasn't already been wrapped in HTML tags
        html = html.replace(/^(?!<[h|o|u|d|p])[^<\n](.+)$/gm, '<p class="article-paragraph">$&</p>');
        
        // Restore code blocks
        codeBlocks.forEach((block, i) => {
            const language = block.match(/```([a-z]*)\n/)?.[1] || '';
            const code = block.replace(/```([a-z]*)\n/, '').replace(/\n```$/, '');
            html = html.replace(
                `CODE_BLOCK_${i}`,
                `<div class="article-code-block"><div class="code-language">${language}</div><pre>${code}</pre></div>`
            );
        });
        
        // Restore inline code
        inlineCodes.forEach((code, i) => {
            const inlineCode = code.replace(/`/g, '');
            html = html.replace(
                `INLINE_CODE_${i}`,
                `<code class="article-inline-code">${inlineCode}</code>`
            );
        });
        
        // Handle line breaks for better spacing
        html = html.replace(/\n{2,}/g, '</p><p class="article-paragraph">');
        html = html.replace(/\n(?!<\/p>)/g, '<br>');
        
        // Clean up any potentially invalid HTML from the conversions
        html = html.replace(/<\/p><p class="article-paragraph"><(h|ul|ol|div)/g, '<$1');
        html = html.replace(/<\/p><p class="article-paragraph"><\/(h|ul|ol|div)/g, '</$1');
        
        // Wrap the entire article in a container
        html = `<div class="article-container">${html}</div>`;
        
        return html;
    }

    // Handle copy to clipboard for raw markdown
    copyRawBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(markdownOutput.textContent)
            .then(() => {
                alert('Raw markdown copied to clipboard!');
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                alert('Failed to copy to clipboard. Please try again.');
            });
    });

    // Handle copy to clipboard for article text (formatted)
    copyArticleBtn.addEventListener('click', () => {
        // Create a hidden textarea with rich text
        const articleContainer = document.createElement('div');
        articleContainer.innerHTML = previewContainer.innerHTML;

        // Create a range and selection
        const selection = window.getSelection();
        const range = document.createRange();
        
        // Append to body temporarily (required for copying)
        document.body.appendChild(articleContainer);
        range.selectNodeContents(articleContainer);
        selection.removeAllRanges();
        selection.addRange(range);
        
        // Execute copy command
        const successful = document.execCommand('copy');
        
        // Clean up
        selection.removeAllRanges();
        document.body.removeChild(articleContainer);
        
        if (successful) {
            alert('Formatted article copied to clipboard! You can now paste it into Word or another application.');
        } else {
            alert('Failed to copy to clipboard. Please try again or use another method.');
        }
    });

    // Handle download as markdown
    downloadMdBtn.addEventListener('click', () => {
        // Get feature name from whichever form is active
        let featureName = '';
        if (featureForm.style.display !== 'none') {
            featureName = document.getElementById('feature-name').value;
        } else if (specForm.style.display !== 'none') {
            featureName = document.getElementById('feature-name-spec').value;
        } else {
            featureName = document.getElementById('feature-name-screenshot').value;
        }
        
        const filename = featureName.toLowerCase().replace(/\s+/g, '-') + '.md';
        const blob = new Blob([markdownOutput.textContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Handle back button
    backBtn.addEventListener('click', () => {
        document.querySelector('.input-section').style.display = 'block';
        outputSection.style.display = 'none';
    });

    /**
     * Generate markdown documentation from direct spec input
     */
    function generateMarkdownFromSpec(featureName, category, docType, specText) {
        let markdown = '';
        
        // Title
        markdown += `# ${featureName}\n\n`;
        
        // Add the spec text as the main content
        markdown += `${specText}\n\n`;
        
        // Add navigation and placement information
        markdown += `## Documentation placement\n\n`;
        markdown += `This documentation should be placed in the following location in the Dev Box documentation structure:\n\n`;
        markdown += `- Category: ${formatCategoryName(category)}\n`;
        markdown += `- Documentation Type: ${docType.toUpperCase()}\n`;
        markdown += `- Suggested URL: \`/azure/dev-box/${featureName.toLowerCase().replace(/\s+/g, '-')}\`\n\n`;

        // Add next steps
        markdown += `## Next steps\n\n`;
        markdown += `- Explore other [Dev Box features](https://learn.microsoft.com/azure/dev-box/)\n`;
        markdown += `- Learn about [Microsoft Dev Box concepts](https://learn.microsoft.com/azure/dev-box/microsoft-dev-box-concepts)\n\n`;

        return markdown;
    }

    /**
     * Generate markdown documentation based on user inputs
     */
    function generateMarkdown(
        featureName, 
        category,
        docType, 
        featureDesc, 
        prerequisites, 
        configSteps, 
        screenshots, 
        bestPractices, 
        limitations
    ) {
        let markdown = '';
        
        // Title
        markdown += `# ${featureName}\n\n`;
        
        // Description
        markdown += `${featureDesc}\n\n`;

        // Prerequisites (if provided)
        if (prerequisites.trim()) {
            markdown += `## Prerequisites\n\n${prerequisites}\n\n`;
        }

        // Configuration steps
        markdown += `## How to use ${featureName}\n\n`;
        
        // Process the configuration steps - split by newlines and format as numbered steps
        const steps = configSteps.split('\n').filter(step => step.trim());
        if (steps.length > 0) {
            markdown += "Follow these steps to configure and use this feature:\n\n";
            steps.forEach((step, index) => {
                markdown += `${index + 1}. ${step.trim()}\n`;
            });
            markdown += '\n';
        } else {
            markdown += `${configSteps}\n\n`;
        }

        // Screenshots (if provided)
        if (screenshots.trim()) {
            markdown += `## Screenshots\n\n`;
            const screenshotsList = screenshots.split('\n').filter(item => item.trim());
            screenshotsList.forEach(item => {
                markdown += `- ${item.trim()}\n`;
            });
            markdown += '\n> [!NOTE]\n> Actual screenshots should be added to the documentation during the publishing process.\n\n';
        }

        // Best practices (if provided)
        if (bestPractices.trim()) {
            markdown += `## Best practices\n\n${bestPractices}\n\n`;
        }

        // Limitations (if provided)
        if (limitations.trim()) {
            markdown += `## Known limitations\n\n${limitations}\n\n`;
        }

        // Add navigation and placement information
        markdown += `## Documentation placement\n\n`;
        markdown += `This documentation should be placed in the following location in the Dev Box documentation structure:\n\n`;
        markdown += `- Category: ${formatCategoryName(category)}\n`;
        markdown += `- Documentation Type: ${docType.toUpperCase()}\n`;
        markdown += `- Suggested URL: \`/azure/dev-box/${featureName.toLowerCase().replace(/\s+/g, '-')}\`\n\n`;

        // Add next steps
        markdown += `## Next steps\n\n`;
        markdown += `- Explore other [Dev Box features](https://learn.microsoft.com/azure/dev-box/)\n`;
        markdown += `- Learn about [Microsoft Dev Box concepts](https://learn.microsoft.com/azure/dev-box/microsoft-dev-box-concepts)\n\n`;

        return markdown;
    }

    /**
     * Format the category name for documentation placement
     */
    function formatCategoryName(category) {
        const categoryMap = {
            'overview': 'Overview',
            'deploy': 'Deploy',
            'get-started': 'Get Started',
            'cost-management': 'Dev Box Cost Management',
            'secure-access': 'Provide Secure Access',
            'custom-dev-boxes': 'Create Custom Dev Boxes',
            'support': 'Support & Reference'
        };
        
        return categoryMap[category] || category;
    }

    /**
     * Convert markdown to simple HTML for the preview
     */
    function convertMarkdownToHTML(markdown) {
        if (!markdown) return '';
        
        let html = markdown;
        
        // Headers
        html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        
        // Paragraphs
        html = html.replace(/^(?!<h[1-6]>)(?!\d\. )(?!\- )(.+)$/gm, '<p>$1</p>');
        
        // Lists
        // Numbered lists
        html = html.replace(/^(\d\. .*)$/gm, '<li>$1</li>');
        // Bullet lists
        html = html.replace(/^(\- .*)$/gm, '<li>$1</li>');
        
        // Wrap lists with ul/ol elements
        // This is a simplified approach and might not work for all cases
        html = html.replace(/(<li>\d\. .*<\/li>(\n|$))+/g, '<ol>$&</ol>');
        html = html.replace(/(<li>\- .*<\/li>(\n|$))+/g, '<ul>$&</ul>');
        
        // Notes
        html = html.replace(/> \[!NOTE\]\n> (.*)/g, '<div class="note"><strong>NOTE:</strong> $1</div>');
        
        // Line breaks
        html = html.replace(/\n/g, '');
        
        return html;
    }

    /**
     * Enhance documentation with Azure OpenAI via the Python backend
     */
    async function enhanceWithAzureOpenAI(markdown, featureName, category, docType, enhancementType) {
        // Prepare request data
        const requestData = {
            markdown: markdown,
            featureName: featureName,
            category: category,
            docType: docType,
            enhancementType: enhancementType
        };
        
        // Call the Flask server endpoint
        const response = await fetch(`${serverConfig.serverUrl}/api/enhance-documentation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to enhance documentation');
        }
        
        const result = await response.json();
        return result.enhancedMarkdown;
    }
});