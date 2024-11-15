from flask import Flask, request, jsonify, render_template_string
from openai import AzureOpenAI

app = Flask(__name__)

# Initialize the AzureOpenAI client
client = AzureOpenAI(
    api_key="",  
    api_version="2024-10-21",
    azure_endpoint="https://demo.openai.azure.com"
)


def translate_text(text, source_language, target_language):
    system_message = f"""
You are a professional translator proficient in translating {source_language} text into {target_language}.
Your task is to provide an accurate and natural-sounding translation of the given {source_language} text into {target_language}.

Instructions:
- Only provide the translated text.
- Do not include the original {source_language} text.
- Do not add any explanations, notes, or extra information.
- Do not start or end the response with phrases like 'Translation:', 'Here is the translation:', etc.
- Ensure proper grammar, spelling, and punctuation in {target_language}.
- Preserve the original meaning and tone of the text.

If the text contains idioms, expressions, or cultural references, translate them appropriately so they make sense to a native {target_language} speaker.
"""

    user_input = text

    response = client.chat.completions.create(
        model="gpt-4",  # Replace with your desired model
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_input.strip()}
        ],
        max_tokens=1000,  # Adjust if you expect longer translations
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON input'}), 400
    source_text = data.get('source_text')
    source_language = data.get('source_language')
    target_language = data.get('target_language')

    if source_language == 'Select one' or target_language == 'Select one':
        return jsonify({'error': 'Please select both source and target languages'}), 400
    if not source_text or not source_language or not target_language:
        return jsonify({'error': 'Invalid input parameters'}), 400

    translated_text = translate_text(source_text, source_language, target_language)

    return jsonify({
        'original': source_text,
        'translated': translated_text,
        'source_language': source_language,
        'target_language': target_language
    })

@app.route('/demo', methods=['GET'])
def demo():
    languages = [
        'English', 'Spanish', 'French', 'German', 'Italian', 'Chinese', 'Japanese',
        'Korean', 'Russian', 'Portuguese', 'Arabic'
    ]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>LLM Translator Demo</title>
    <!-- Bootstrap CSS -->
    <link
      rel="stylesheet"
      href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css"
    />
    <style>
        body {
            background-color: #f8f9fa;
        }
        .translator-container {
            margin-top: 50px;
        }
        .card {
            border-radius: 15px;
        }
        .translate-button {
            width: 100%;
            font-size: 18px;
            padding: 10px;
        }
        #loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .fade-in {
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .custom-select, .form-control {
            height: calc(2.25rem + 12px);
            border-radius: 0.5rem;
        }
        .textarea-resize-none {
            resize: none;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <!-- jQuery and Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script
      src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"
    ></script>
</head>
<body>
    <div class="container translator-container">
        <h1 class="text-center mb-5">LLM-Powered Translator Demo</h1>
        <div class="row">
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">Source Text</h5>
                            <select id="source_language" class="custom-select w-auto" onchange="updateTargetLanguages()">
                                <option selected disabled>Select one</option>
                                {% for lang in languages %}
                                    <option value="{{ lang }}">{{ lang }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <textarea id="source_text" class="form-control textarea-resize-none mt-3" rows="10" placeholder="Enter source text here..."></textarea>
                    </div>
                </div>
            </div>
            <div class="col-md-2 text-center my-auto">
                <button id="swap_languages" class="btn btn-outline-secondary btn-lg mb-3" disabled>
                    <i class="fas fa-exchange-alt"></i>
                </button>
            </div>
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">Translated Text</h5>
                            <select id="target_language" class="custom-select w-auto">
                                <option selected disabled>Select one</option>
                                {% for lang in languages %}
                                    <option value="{{ lang }}">{{ lang }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <textarea id="translated_text" class="form-control textarea-resize-none mt-3" rows="10" placeholder="Translation will appear here..." readonly></textarea>
                    </div>
                </div>
            </div>
        </div>
        <div class="row mt-4">
            <div class="col text-center">
                <button class="btn btn-primary translate-button" id="translate_button">Translate</button>
                <hr />
                <button id="check_in_google" class="btn btn-secondary" onclick="openGoogleTranslate()">Check in Google</button>
            </div>
        </div>
        <div id="loading">
            <div class="spinner-border text-primary" role="status">
              <span class="sr-only">Translating...</span>
            </div>
            <p class="mt-2">Translating...</p>
        </div>
    </div>
    <!-- Font Awesome for Icons -->
    <script
      src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/js/all.min.js"
      crossorigin="anonymous"
    ></script>
    <script>
        var languages = {{ languages | tojson }};
        var languageCodes = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Chinese': 'zh-CN',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Russian': 'ru',
            'Portuguese': 'pt',
            'Arabic': 'ar'
        };
        function updateTargetLanguages() {
            var sourceLanguage = $('#source_language').val();
            var targetLanguageSelect = $('#target_language');
            targetLanguageSelect.empty();
            targetLanguageSelect.append('<option selected disabled>Select one</option>');
            for (var i = 0; i < languages.length; i++) {
                if (languages[i] !== sourceLanguage) {
                    targetLanguageSelect.append('<option value="' + languages[i] + '">' + languages[i] + '</option>');
                }
            }
        }
        function openGoogleTranslate() {
            var sourceText = document.getElementById('source_text').value;
            var sourceLanguage = $('#source_language').val();
            var targetLanguage = $('#target_language').val();

            var sourceCode = languageCodes[sourceLanguage];
            var targetCode = languageCodes[targetLanguage];

            if (!sourceCode || !targetCode) {
                alert('Please select both source and target languages.');
                return;
            }

            var url = "https://translate.google.com/?hl=en&sl=" + sourceCode + "&tl=" + targetCode + "&text=" + encodeURIComponent(sourceText);
            window.open(url, '_blank');
        }
        $(document).ready(function() {
            $('#translate_button').click(function() {
                var sourceText = $('#source_text').val().trim();
                var sourceLanguage = $('#source_language').val();
                var targetLanguage = $('#target_language').val();

                if (sourceText === '') {
                    $('#source_text').addClass('is-invalid');
                    return;
                } else {
                    $('#source_text').removeClass('is-invalid');
                }

                $('#translated_text').val('');
                $('#loading').fadeIn();

                $.ajax({
                    url: '/translate',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        source_text: sourceText,
                        source_language: sourceLanguage,
                        target_language: targetLanguage
                    }),
                    success: function(response) {
                        $('#loading').fadeOut();
                        $('#translated_text').val(response.translated).addClass('fade-in');
                    },
                    error: function() {
                        $('#loading').fadeOut();
                        alert('An error occurred while translating. Please try again.');
                    }
                });
            });

            $('#source_text').on('input', function() {
                if ($(this).val().trim() !== '') {
                    $(this).removeClass('is-invalid');
                }
            });
        });
    </script>
</body>
</html>
""", languages=languages)

if __name__ == '__main__':
    app.run(debug=True)
