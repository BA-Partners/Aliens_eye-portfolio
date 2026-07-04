module.exports = {
  apps: [
    {
      name: 'local-qwen-service',
      script: '/Users/nana-520/llama.cpp-master/build/bin/llama-server',
      args: [
        '-m', '/Users/nana-520/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct-GGUF/snapshots/bb5d59e06d9551d752d08b292a50eb208b07ab1f/qwen2.5-7b-instruct-q3_k_m.gguf',
        '--port', '8080',
        '--host', '0.0.0.0',
        '-t', '4',
        '-tb', '4',
        '-ngl', '99',
        '-b', '512',
      ],
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      exp_backoff_restart_delay: 100,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/Users/nana-520/llama.cpp-master/Aliens_eye/.pm2/logs/local-qwen-service-error.log',
      out_file: '/Users/nana-520/llama.cpp-master/Aliens_eye/.pm2/logs/local-qwen-service-out.log',
      merge_logs: true,
      env: {
        LLAMA_ARG_N_GPU_LAYERS: '99',
        LLAMA_ARG_BATCH: '512',
      }
    }
  ]
};
