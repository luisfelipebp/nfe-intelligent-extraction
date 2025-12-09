import torch
from datasets import load_from_disk
from transformers import AutoModelForTokenClassification, TrainingArguments, Trainer
from transformers import DataCollatorForTokenClassification
from transformers import AutoProcessor
import numpy as np
import evaluate
import warnings
warnings.filterwarnings("ignore")

DATASET_PATH = "processed_dataset" 
OUTPUT_DIR = "layoutlmv3-finetuned-nfe"

NUM_EPOCHS = 15
BATCH_SIZE = 2
LEARNING_RATE = 0.00002

LABELS_LIST = [
    "O", 
    "CHAVE_ACESSO", 
    "NOME_EMITENTE", 
    "CNPJ_EMITENTE",
    "NOME_DESTINATARIO", 
    "CNPJ_DESTINATARIO", 
    "DATA_EMISSAO", 
    "VALOR_TOTAL", 
    "NUM_NOTA_FISCAL", 
    "NUM_SERIE"
]

id2label = {i: label for i, label in enumerate(LABELS_LIST)}
label2id = {label: i for i, label in enumerate(LABELS_LIST)}

print("Carregando dataset...")
try:
    full_dataset = load_from_disk(DATASET_PATH)
    
    dataset_split = full_dataset.train_test_split(test_size=0.2, seed=7)
    
    train_dataset = dataset_split["train"]
    eval_dataset = dataset_split["test"]
    
    print(f"Dataset dividido com sucesso:")
    print(f" -> Imagens de Treino: {len(train_dataset)}")
    print(f" -> Imagens de Teste:  {len(eval_dataset)}")

except Exception as e:
    print(f"Erro ao carregar dataset: {e}")
    exit()

print("Carregando Processor e Modelo...")
processor = AutoProcessor.from_pretrained("microsoft/layoutlmv3-base", apply_ocr=False)
model = AutoModelForTokenClassification.from_pretrained(
    "microsoft/layoutlmv3-base",
    num_labels=len(LABELS_LIST),
    id2label=id2label,
    label2id=label2id
)

metric = evaluate.load("seqeval")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [LABELS_LIST[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [LABELS_LIST[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    fp16=True,                
    dataloader_num_workers=0, 
    logging_steps=10,          
    save_strategy="epoch",
    save_total_limit=1,       
    eval_strategy="epoch", 
    remove_unused_columns=False 
)


data_collator = DataCollatorForTokenClassification(
    tokenizer=processor.tokenizer,
    padding="longest",
    return_tensors="pt"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=processor,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

print(f"Iniciando treinamento na GPU: {torch.cuda.get_device_name(0)}")
trainer.train()

trainer.save_model(OUTPUT_DIR)
processor.save_pretrained(OUTPUT_DIR) 
print(f"Sucesso! Modelo salvo em: {OUTPUT_DIR}")