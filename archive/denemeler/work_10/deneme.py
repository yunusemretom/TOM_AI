from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


tokenizer = AutoTokenizer.from_pretrained("vngrs-ai/VBART-Medium-Base")
model = AutoModelForSeq2SeqLM.from_pretrained("vngrs-ai/VBART-Medium-Base")
# Metni tokenle
input_text = "bir sorun mu var"
inputs = tokenizer(input_text, return_tensors="pt")
inputs.pop("token_type_ids")  # Bu satırı ekle
output = model.generate(**inputs)



# Sonucu çözüp yazdır
decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
print(decoded_output)
